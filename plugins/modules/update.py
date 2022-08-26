#!/usr/bin/python
# coding: utf-8
from __future__ import absolute_import, division, print_function

# (c) 2021, Johanna Dorothea Reichmann <transcaffeine@finally.coffee>
# (c) 2021, Famedly GmbH
# GNU Affero General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/agpl-3.0.txt)

__metaclass__ = type

DOCUMENTATION = r"""
---
module: update
author:
- Johanna Dorothea Reichmann (@jdreichmann)
requirements:
    - python >= 3.9
    - dnspython >= 2.1.0
short_description: Update DNS records using DNSUPDATE (RFC2136)
description:
    - "Allows updating DNS RR sets using DNSUPDATE messages as described in RFC2136"
options:
    primary_master:
        description: IP address of the primary master, where DNSUPDATE messages get sent to
        type: str
        required: true
    zone:
        description: The DNS zone to modify using DNSUPDATE
        type: str
        required: true
    rr_set:
        description: A list of dicts of the form {name, type, content, ?ttl}
                     describing the set of resource records to modify.
                     Note that the content _always_ needs to be fully qualified or idempotency can not be guaranteed,
                     the module will not attempt to make names in the content absolute.
        type: dict
        suboptions:
            name:
                description: beep
                type: str
                required: true
            type:
                description: beep
                type: str
                required: true
            content:
                description: beep
                type: str
                required: true
            ttl:
                description: beep
                type: int
                default: 3600
        required: true
    tsig_key:
        description: The TSIG key to use to sign the transaction
        type: str
        required: true
    tsig_algo:
        description: The algorithm of the TSIG key to be used, usually hmac-sha256
        type: str
        required: true
    tsig_name:
        description: The TSIG key's name
        type: str
        default: default
        required: false
    state:
        description: Whether to add or remove the records, or make sure the zone matches the provided recordset exactly
        type: str
        choices: [present, absent, exact]
        default: present
        required: false
"""

EXAMPLES = r"""
- name: Set multiple records for a new host
  famedly.dns.update:
    primary_master: ns0.famedly.de
    zone: myzone.example.com
    tsig_key: <secret>
    tsig_algo: <algo> # for example, `hmac-sha256`
    rr_set:
      - name: "service"
        type: CNAME
        content: "host.myzone.example.com"
      - name: host
        type: A
        content: 127.0.0.1
      - name: host
        type: AAAA
        content: fe80::1
    state: present
"""

RETURN = r"""
added:
    description: The added records
    returned: When records were added to the zone
    type: list
    elements: dict
deleted:
    description: The deleted records
    returned: When records were deleted from the zone
    type: list
    elements: dict

"""

import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

from dataclasses import asdict

LIB_IMP_ERR = None
try:
    from ansible_collections.famedly.dns.plugins.module_utils.dnsupdate_utils import (
        ResourceRecord,
        make_rr_set_absolute,
        primary_master_to_ip_literal,
        get_resource_records,
        get_resolver_for_ip,
        get_diff_rr_set,
        send_dns_update_message,
        get_keyring,
    )

    HAS_LIB = True
except ImportError:
    HAS_LIB = False
    LIB_IMP_ERR = traceback.format_exc()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            zone=dict(required=True, type="str"),
            primary_master=dict(required=True, type="str"),
            tsig_name=dict(type="str", required=False, default="default"),
            tsig_key=dict(required=True, type="str", no_log=True),
            tsig_algo=dict(required=True, type="str"),
            rr_set=dict(
                required=True,
                type="dict",
                options=dict(
                    type=dict(type="str", required=True),
                    name=dict(type="str", required=True),
                    content=dict(type="str", required=True),
                    ttl=dict(type="int", required=False, default=3600),
                ),
            ),
            state=dict(
                type="str",
                required=False,
                default="present",
                choices=["present", "absent", "exact"],
            ),
        ),
        supports_check_mode=True,
    )

    result = dict(changed=False, diff={}, message="")

    failed = False

    if not HAS_LIB:
        module.fail_json(msg=missing_required_lib("dnspython"), exception=LIB_IMP_ERR)

    zone: str = module.params["zone"]
    target_state = [
        ResourceRecord(rr["name"], rr["type"].upper(), rr["content"], int(rr["ttl"]))
        for rr in make_rr_set_absolute(module.params["rr_set"], zone)
    ]

    # Resolve `primary_master` argument to a reachable IP
    server_ip: str = primary_master_to_ip_literal(module.params["primary_master"])
    if not server_ip:
        failed = True
        result[
            "message"
        ] = f"No reachable IP or IPv4 address found for {module.params['primary_master']}, connection probing done with port 53/tcp."
        module.fail_json(**result)

    # Get existing RRs first
    existing_rr_set = get_resource_records(target_state, get_resolver_for_ip(server_ip))

    # Build the add/delete list
    diff_set = get_diff_rr_set(existing_rr_set, target_state, module.params["state"])

    # Send the DNSUPDATE message signed with the provided key
    tsig_keyring = get_keyring(module.params["tsig_name"], module.params["tsig_key"])
    if not module.check_mode:
        (success, reason) = send_dns_update_message(
            zone, tsig_keyring, diff_set, server_ip
        )
        if not success:
            failed = True
        result["msg"] = reason

    dns_diff = dict(
        before="\n".join(
            [
                "\t\t".join([r.name, r.typ, r.content])
                for r in existing_rr_set
                if r not in diff_set.add
            ]
        )
        + "\n",
        after="\n".join(
            [
                "\t\t".join([r.name, r.typ, r.content])
                for r in target_state
                if r and r not in diff_set.delete
            ]
        )
        + "\n",
    )

    result["diff"] = {
        "before_header": f"DNS {zone}",
        "after_header": f"DNS {zone}",
        "before": dns_diff["before"],
        "after": dns_diff["after"],
    }
    # "counts" the changes, as n > 0 == true, this shows `changed` when any entry will be changed
    result["changed"] = len(diff_set.add) + len(diff_set.delete)
    result["added"] = [asdict(rr) for rr in diff_set.add]
    result["deleted"] = [asdict(rr) for rr in diff_set.delete]

    if failed:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == "__main__":
    main()
