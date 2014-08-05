
import os
import re
import requests
import subprocess
import tempfile
import time
import uuid

#import local_env as e
import test_lb_base as lb


class NeutronLBV1(lb.NeutronBaseLB):

    def __init__(self, lb_method='ROUND_ROBIN', protocol='HTTP'):
        super(NeutronLBV1, self).__init__()
        self.lb_pool_create(self.pool_name, self.instance_subnet_id,
                            lb_method, protocol)

    # method: None, ROUND_ROBIN, LEAST_CONNECTIONS, SOURCE_IP
    # protocol: HTTP, HTTPS, TCP
    def lb_pool_create(self, pool_name, subnet_id, method='ROUND_ROBIN',
                       protocol='HTTP'):
        self._neutron(['lb-pool-create', '--name', pool_name,
                       '--lb-method', method, '--protocol', protocol,
                       '--subnet-id', subnet_id])
        self._wait_for_completion(['lb-pool-show', pool_name])

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
        # port_id = find(r, "^\| port_id.*\| ([^\s]+)")
        self.vip_id = find(r, "^\| id.*\| ([^\s]+)")
        self.vip_ip = find(r, "^\| address.*\| ([^\s]+)")
        print("INTERNAL VIP_IP ", self.vip_ip)
        self._wait_for_completion(['lb-vip-show', self.vip_name])

    def vip_destroy(self):
        self._neutron(['lb-vip-delete', self.vip_name])

    def member_create(self, ip_address, port=80):
        r = self._neutron(['lb-member-create', '--address', ip_address,
                           '--protocol-port', str(port), self.pool_name])
        member_id = find(r, "^\| id.*\| ([^\s]+)")
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
        self.monitor_id = find(r, "^\| id.*\| ([^\s]+)")

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
        member_list = [e.MEMBER1_IP, e.MEMBER2_IP]
        for ip in member_list:
            self.member_destroy(ip)
        self.vip_destroy()
        self.pool_delete()



#
# Tests
#

def setup_lb(lb_method, protocol, persistence):
    lb = NeutronLB(lb_method=lb_method, protocol=protocol)

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

    member_list = [e.MEMBER1_IP, e.MEMBER2_IP]
    for ip in member_list:
        lb.member_create(ip)

    lb.monitor_create()
    lb.monitor_associate()
    return lb


def pull_data(url_base, vip_ip):
    member_list = [e.MEMBER1_IP, e.MEMBER2_IP]
    members = {}
    # for ip in member_list:
    #     members[ip] = requests.get("http://%s/" % ip).text

    url = url_base % vip_ip
    print("LB URL %s", url)
    lb_data = requests.get(url, verify=False).text
    print("DATA LB ++%s++" % lb_data)

    # matching_data = False
    # for ip, data in members.items():
    #     if data == lb_data:
    #         matching_data = True
    #         break

    # assert matching_data
    if lb_data == "":
        raise "failed to pull data"


def end_to_end(lb_method, protocol, persistence, url_base):
    e.demo_creds()

    # Step 1, setup LB via neutron
    lb = setup_lb(lb_method, protocol, persistence)

    # Step 3, pull some data through the LB and verify
    if pull_data_arg:
        pull_data(url_base, lb.vip_ip)

    # Whoa, all done, success.
    lb.destroy()


def test_lb():
    end_to_end('ROUND_ROBIN', 'HTTP', None, 'http://%s/')


def test_lb_matrix():
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
                end_to_end(method, protocol, persistence, url_base)

def run_tests(parser):
    #test_lb()
    test_lb_matrix()
