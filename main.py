#!/usr/bin/env python3
import re
import yaml
from collections import namedtuple, defaultdict
from ipaddress import IPv4Network
from itertools import repeat


BoundIface = namedtuple('BoundIface', 'host iface')
DomainAsoc = namedtuple('DomainAsoc', 'iface domain')

IFACE_STATEMENT_REGEXP = r'([a-z0-9_]+)\[(\d+)\]\s*=\s*"([A-Z])'


def get_conf_contents(path="./lab.conf"):
    with open(path) as f:
        raw = f.readlines()

    stripped = map(lambda l: l.rstrip("\n"), raw)
    return filter(bool, stripped)


def parse_iface_statement(statement):
    result = re.match(IFACE_STATEMENT_REGEXP, statement)

    if result:
        host, iface, domain = result.groups()
        return DomainAsoc(iface=BoundIface(host=host, iface=iface), domain=domain)
    else:
        raise ValueError("Not an iface statement")


def get_domain_subnets(path="./subnets.yml"):
    return {k: IPv4Network(v) for k, v in yaml.safe_load(open(path)).items()}


def main():
    domains = defaultdict(list)
    subnets = get_domain_subnets()
    contents = get_conf_contents()
    ble = []

    for statement in contents:
        try:
            dasc = parse_iface_statement(statement)
            domains[dasc.domain].append(dasc.iface)
        except ValueError:
            continue

    # TODO: Refactor this crap

    for domain, iface in domains.items():
        subnet = subnets[domain]

        ble += zip(subnet.hosts(), iface, repeat(subnet.netmask))

    for i in ble:
        fe_template = "ifconfig eth{ifno} {ip} netmask {netmask} up" 
        fe = fe_template.format(ifno=i[1].iface, ip=i[0], netmask=i[2])

        argh_template = "echo '{command}' >> {host}.startup"
        argh = argh_template.format(command=fe, host=i[1].host)
        print(argh)

if __name__ == "__main__":
    # TODO: Add Click CLI
    main()
