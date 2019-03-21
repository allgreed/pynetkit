import re

import pytest

from main import NetedIface


ping_result_regexp = re.compile(r"--- ((\d{1,3}\.*){4}).*\n1 packets transmitted, (\d)", re.MULTILINE)

hosts = ["pc1", "pc2", "pc3", "pc4", "pc5", "pc6" ,"r1", "r2"]

def get_pings_for(host):
    with open("/opt/netkit/tasks/static-1/_test/%s.test" % host) as f:
        contents = f.readlines()

        pings = [line for line in contents if line.lstrip().startswith("ping")]

        return pings

def get_results_for(host):
    with open("/opt/netkit/tasks/static-1/_test/results/%s.user" % host) as f:
        contents = f.read() 

        # TODO: Refactor
        ble = []
        for match in re.findall(ping_result_regexp, contents):
            dest, _, success = match
            ble.append((host, dest, int(success)))

        print(host, len(ble))
        return ble

all_results = sum([get_results_for(host) for host in hosts], [])
all_pings = sum([get_pings_for(host) for host in hosts], [])

def test_all_pings_were_performed():
    # TODO: Report which pings were not performed
    assert len(all_pings) == len(all_results)

@pytest.mark.parametrize("src, dest, success", all_results)
def test_connectivity(src, dest, success):
    assert success, "No connectivity between {src} and {dest}".format(src=src, dest=dest)
