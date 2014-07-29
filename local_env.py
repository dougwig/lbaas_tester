# Configuration for this neutron network node!

import os

PATH_TO_ADMIN_OPENRC = os.path.join(os.environ['HOME'], 'admin-openrc.sh')
PATH_TO_DEMO_OPENRC = os.path.join(os.environ['HOME'], 'demo-openrc.sh')

INSTANCE_NETWORK_NAME = 'private'
LB_NETWORK_NAME = 'public'

MEMBER1_IP = '192.168.2.62'
MEMBER2_IP = '192.168.2.61'


def source_env(path):
    for line in open(path):
        name, value = line.split('=')
        if name[:7] == "export ":
            name = name[7:]
        os.environ[name] = value.rstrip()


def demo_creds():
    source_env(PATH_TO_DEMO_OPENRC)


def admin_creds():
    source_env(PATH_TO_ADMIN_OPENRC)
