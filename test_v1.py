# Copyright 2014, Doug Wiegley (dougwig), A10 Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import requests

import test_lb_base as lb


class NeutronLBV1(lb.NeutronBaseLB):

    # method: None, ROUND_ROBIN, LEAST_CONNECTIONS, SOURCE_IP
    # protocol: HTTP, HTTPS, TCP
    def pool_create(self, method='ROUND_ROBIN', protocol='HTTP'):
        self._neutron(['lb-pool-create', '--name', self.pool_name,
                       '--lb-method', method, '--protocol', protocol,
                       '--subnet-id', self.instance_subnet_id])
        self._wait_for_completion(['lb-pool-show', self.pool_name])

    def pool_delete(self):
        r = self._neutron(['lb-pool-delete', self.pool_name])
        assert r.strip() == "Deleted pool: %s" % self.pool_name

    # protocol: TCP, HTTP, HTTPS
    # persistence: None, HTTP_COOKIE, SOURCE_IP, APP_COOKIE
    def vip_create(self, port=80, protocol='HTTP', persistence=None):
        self.vip_name = self._random_hex()
        a = ['lb-vip-create', '--name', self.vip_name,
             '--protocol', protocol,
             '--protocol-port', str(port),
             '--subnet-id', self.lb_subnet_id, self.pool_name]
        if persistence is not None:
            a.append('--session-persistence')
            a.append('type=dict')
            if persistence is 'APP_COOKIE':
                a.append("type=%s,cookie_name=mycookie" % persistence)
            else:
                a.append("type=%s" % persistence)
        r = self._neutron(a)
        # port_id = self._find(r, "^\| port_id.*\| ([^\s]+)")
        self.vip_id = self._find(r, "^\| id.*\| ([^\s]+)")
        self.vip_ip = self._find(r, "^\| address.*\| ([^\s]+)")
        print("INTERNAL VIP_IP ", self.vip_ip)
        self._wait_for_completion(['lb-vip-show', self.vip_name])

    def vip_destroy(self):
        self._neutron(['lb-vip-delete', self.vip_name])

    def member_create(self, ip_address, port=80):
        r = self._neutron(['lb-member-create', '--address', ip_address,
                           '--protocol-port', str(port), self.pool_name])
        member_id = self._find(r, "^\| id.*\| ([^\s]+)")
        self._wait_for_completion(['lb-member-show', member_id])
        self.members[ip_address] = member_id

    def member_destroy(self, ip_address):
        self._neutron(['lb-member-delete', self.members[ip_address]])

    # expected: 200, 200-299, 200,201
    # http_method: GET, POST
    # url_path: URL, "/"
    # mon_type: PING, TCP, HTTP, HTTPS
    def monitor_create(self, delay=5, retries=5, timeout=5, mon_type='HTTP'):
        r = self._neutron(['lb-healthmonitor-create', '--delay', str(delay),
                           '--max-retries', str(retries),
                           '--timeout', str(timeout),
                           '--type', mon_type])
        self.monitor_id = self._find(r, "^\| id.*\| ([^\s]+)")

    def monitor_destroy(self):
        self._neutron(['lb-healthmonitor-delete', self.monitor_id])

    def monitor_associate(self):
        r = self._neutron(['lb-healthmonitor-associate', self.monitor_id,
                           self.pool_name])
        assert r.strip() == "Associated health monitor %s" % self.monitor_id

    def monitor_disassociate(self):
        self._neutron(['lb-healthmonitor-disassociate', self.monitor_id,
                       self.pool_name])

    def destroy(self):
        self.monitor_disassociate()
        self.monitor_destroy()
        for ip in self.members.keys():
            self.member_destroy(ip)
        self.vip_destroy()
        self.pool_delete()


def setup_lb(member_list, opts, lb_method, protocol, persistence):
    lb = NeutronLBV1(opts.lb_subnet_name, opts.instance_subnet_name)
    lb.pool_create(lb_method, protocol)

    if protocol == 'HTTP':
        port = 80
    elif protocol == 'HTTPS':
        port = 443
    elif protocol == 'TCP':
        port = 4040
    else:
        print("ERROR: protocol=%s", protocol)
        raise "how did we get here?"

    lb.vip_create(port=port, protocol=protocol, persistence=persistence)

    for ip in member_list:
        lb.member_create(ip)

    lb.monitor_create()
    lb.monitor_associate()
    return lb


def pull_data(member_list, url_base, vip_ip):
    members = {}
    for ip in member_list:
        members[ip] = requests.get("http://%s/" % ip).text

    url = url_base % vip_ip
    print("LB URL %s", url)
    lb_data = requests.get(url, verify=False).text
    print("DATA LB ++%s++" % lb_data)

    matching_data = False
    for ip, data in members.items():
        if data == lb_data:
            matching_data = True
            break

    assert(matching_data)


def end_to_end(member_list, opts, lb_method, protocol, persistence, url_base):
    # Step 1, setup LB via neutron
    lb = setup_lb(member_list, lb_method, protocol, persistence)

    # Step 3, pull some data through the LB and verify
    if opts.pull_data:
        pull_data(member_list, url_base, lb.vip_ip)

    # Whoa, all done, success.
    lb.destroy()


def test_lb(member_list, opts):
    end_to_end(member_list, opts, 'ROUND_ROBIN', 'HTTP', None, 'http://%s/')


def test_lb_matrix(member_list, opts):
    protocols = [
        ('HTTP', 'http://%s/'),
        ('TCP', 'http://%s:4040/'),
        ('HTTPS', 'https://%s/')
    ]
    methods = ['ROUND_ROBIN', 'LEAST_CONNECTIONS', 'SOURCE_IP']
    persists = [None, 'HTTP_COOKIE', 'SOURCE_IP']
    for protocol, url_base in protocols:
        for method in methods:
            for persistence in persists:
                end_to_end(member_list, opts, method, protocol, persistence,
                           url_base)


def run_tests(parser):
    for t in [test_lb, test_lb_matrix]:
        t([parser.member1, parser.member2], parser)
