#!/usr/bin/env python3
import re
import yaml
from collections import namedtuple, defaultdict
from ipaddress import IPv4Network
from itertools import repeat
from functools import update_wrapper

import click


BoundIface = namedtuple('BoundIface', 'host if_no')
NetedIface = namedtuple('NetedIface', 'host if_no ip netmask')
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
        host, if_no, domain = result.groups()
        return DomainAsoc(iface=BoundIface(host=host, if_no=if_no), domain=domain)
    else:
        raise ValueError("Not an interface statement")


def get_domain_subnets(path="./subnets.yml"):
    return {k: IPv4Network(v) for k, v in yaml.safe_load(open(path)).items()}


pass_data = click.make_pass_decorator(object)

@click.group()
@click.pass_context
def cli(ctx):
    domains = defaultdict(list)
    subnets = get_domain_subnets()
    contents = get_conf_contents()

    for statement in contents:
        try:
            dasc = parse_iface_statement(statement)
            domains[dasc.domain].append(dasc.iface)
        except ValueError:
            continue

    def net_domain(domain, bound_ifaces):
        subnet = subnets[domain]
        hosts = subnet.hosts()

        return [NetedIface(*iface, next(hosts), subnet.netmask) for iface in bound_ifaces]

    neted_domains = { k: net_domain(k, v) for k, v in domains.items() }

    ctx.obj = neted_domains.values()


@click.command()
@pass_data
def ifup(data):
    for domain in data:
        for i in domain:
            ifcmd_template = "ifconfig eth{ifno} {ip} netmask {netmask} up" 
            ifcmd = ifcmd_template.format(ifno=i.if_no, ip=i.ip, netmask=i.netmask)

            cmd_template = "echo '{command}' >> {host}.startup"
            cmd = cmd_template.format(command=ifcmd, host=i.host)
            print(cmd)


@click.command()
@pass_data
def gateway_routes(data):
    for domain in data:
        router = next(i for i in domain if "r" in i.host)

        default_route_cmd = "route add default gw %s" % router.ip

        for i in domain:
            if "pc" not in i.host:
                continue

            cmd_template = "echo '{command}' >> {host}.startup"
            cmd = cmd_template.format(command=default_route_cmd, host=i.host)

            print(cmd)


def main():
    cli.add_command(ifup)
    cli.add_command(gateway_routes, "gw")

    cli()


if __name__ == "__main__":
    main()
