

class NeutronBaseLB(object):

    def __init__(self):
        self.instance_subnet_id = self.get_subnet_id(e.INSTANCE_NETWORK_NAME)
        self.lb_subnet_id = self.get_subnet_id(e.LB_NETWORK_NAME)
        self.pool_name = self._random_hex()
        self.members = {}

    def _random_hex(self):
        return uuid.uuid4().hex[0:12]

    def _find(self, str, regex):
        m = re.search(regex, str, re.MULTILINE)
        if m is not None:
            return m.group(1)
        else:
            return ""

    def _neutron(self, cmd):
        print("NEUTRON: ", cmd)
        z = subprocess.check_output(["neutron"] + cmd)
        print("result:\n", z)
        return z

    def _wait_for_completion(self, cmd):
        start = time.time()
        now = start
        r = ''
        while ((now - start) < 10):
            r = self._neutron(cmd)
            if find(r, "(PENDING)") != "PENDING":
                break

        if find(r, "(ACTIVE)") == "" and find(r, "(DEFERRED)") == "":
           raise "error: action did not complete successfully"

    def get_subnet_id(self, network_name):
        r = self._neutron(['net-show', network_name])
        return find(r, "^\| subnets.*\| ([^\s]+)")

