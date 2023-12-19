#!/usr/bin/python
# coding: utf-8

# (c) 2021, Johanna Dorothea Reichmann <transcaffeine@finally.coffee>
# (c) 2021, Famedly GmbH
# GNU Affero General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/agpl-3.0.txt)
import ipaddress
from dataclasses import dataclass, field
from socket import create_connection

from dns import name, message, rcode, resolver, tsigkeyring, rrset, update, query

from typing import Union

# Uses system /etc/resolv.conf
default_resolver = resolver.Resolver()


@dataclass(frozen=True)
class ResourceRecord:
    name: str
    typ: str
    content: str
    ttl: int = 3600

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.typ == other.typ
            and self.content == other.content
        )


@dataclass(frozen=True)
class ChangeSet:
    add: list[ResourceRecord] = field(default_factory=list)
    delete: list[ResourceRecord] = field(default_factory=list)


def get_keyring(keyname: str, key: str) -> dict[name.Name, bytes]:
    return tsigkeyring.from_text({keyname: key})


def get_diff_rr_set(
    existing_rr_set: list[ResourceRecord], rr_set: list[ResourceRecord], mode: str
) -> ChangeSet:
    changeset = ChangeSet()
    if mode == "present":
        changeset.add.extend([rr for rr in rr_set if rr not in existing_rr_set])
    elif mode == "absent":
        changeset.delete.extend([rr for rr in rr_set if rr in existing_rr_set])
    elif mode == "exact":
        changeset.add.extend([rr for rr in rr_set if rr not in existing_rr_set])
        changeset.delete.extend([rr for rr in existing_rr_set if rr not in rr_set])
    return changeset


def get_resource_records(
    rr_set: list[ResourceRecord], _resolver: resolver.Resolver = default_resolver
) -> list[ResourceRecord]:
    existing_rrs = []
    for rr in rr_set:
        existing_rrs.extend(get_resource_record(rr, _resolver))
    return existing_rrs


def get_resource_record(
    rr: ResourceRecord, _resolver: resolver.Resolver
) -> list[ResourceRecord]:
    qname: str = rr.name
    qtype: str = rr.typ
    try:
        records = _resolver.resolve(qname, qtype)
        return [ResourceRecord(qname, qtype, str(r)) for r in records]
    except (resolver.NXDOMAIN, resolver.NoAnswer):
        return []


def send_dns_update_message(
    zone: str,
    keyring: dict[name.Name, bytes],
    keyalgorithm: name.Name,
    rr_set: list[ResourceRecord],
    server_ip: str,
) -> tuple[bool, Union[str, None]]:
    updateMessage = update.UpdateMessage(
        zone, keyring=keyring, keyalgorithm=keyalgorithm
    )
    for rr in rr_set.add:
        updateMessage.add(rr.name, rr.ttl, rr.typ, rr.content)
    for rr in rr_set.delete:
        updateMessage.delete(rr.name, rr.typ, rr.content)

    if len(rr_set.add) or len(rr_set.delete):
        response = query.tcp(updateMessage, server_ip)
        return process_dns_update_answer(response, zone, server_ip)
    else:
        return (True, "No changes performed")


def process_dns_update_answer(
    response: message.Message, zone: str, ip: str
) -> tuple[bool, Union[str, None]]:
    response_rcode = response.rcode()
    if response_rcode == rcode.NOERROR:
        return (True, None)
    elif response_rcode == rcode.SERVFAIL:
        return (False, f"DNSUPDATE failed with SERVFAIL")
    elif response_rcode == rcode.NXDOMAIN:
        return (False, f"Domain {zone} not known by server {ip}")
    elif response_rcode == rcode.NOTIMP:
        return (False, f"DNSUPDATE not implemented by server {ip}")
    elif response_rcode == rcode.REFUSED:
        return (False, f"DNSUPDATE refused by server {ip}")
    elif response_rcode == rcode.NOTAUTH:
        return (False, f"Server {ip} is not authoritative for {zone}")
    elif response_rcode == rcode.NOTZONE:
        return (False, f"Atleast one record is not in {zone}")
    elif response_rcode == rcode.BADSIG:
        return (False, f"General TSIG signature failure")
    elif response_rcode == rcode.BADKEY:
        return (False, f"TSIG Key is not recognized by server")
    elif response_rcode == rcode.BADALG:
        return (False, f"TSIG Algorithm not supported by server")
    else:
        return (
            False,
            f"Encountered rcode {response_rcode} ({str(rcode.from_text(response_rcode))})",
        )


def get_resolver_for_ip(ip: str) -> resolver.Resolver:
    resolver_cache = resolver.Cache(cleaning_interval=10)
    _resolver = resolver.Resolver()
    _resolver.nameservers = [ip]
    _resolver.cache = resolver_cache
    return _resolver


def primary_master_to_ip_literal(primary_master: str) -> Union[str, None]:
    if is_ip_literal(primary_master):
        return primary_master
    return resolve_domain_name(primary_master)


def resolve_domain_name(name: str) -> Union[str, None]:
    answer = None
    sock = None
    try:
        answer = str(resolver.resolve(name, "AAAA")[0])
        sock = create_connection((answer, 53), 1)
    except Exception as msg:
        try:
            answer = str(resolver.resolve(name, "A")[0])
            sock = create_connection((answer, 53), 1)
        except Exception as e:
            answer = None
            pass
    finally:
        if sock:
            sock.close()
        return answer


def is_ip_literal(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def make_rr_set_absolute(rr_set: list[dict[str, any]], to: str) -> list[dict[str, any]]:
    zone = name.from_text(to)
    return [make_rr_absolute(rr, zone) for rr in rr_set]


def make_rr_absolute(rr: dict[str, any], zone: name.Name) -> dict[str, any]:
    rname = name.from_text(rr["name"])
    if not rname.is_subdomain(zone):
        rr["name"] = ".".join([rr["name"], str(zone)])
    return rr
