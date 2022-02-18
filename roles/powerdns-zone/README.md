# `famedly.dns.powerdns-zone` ansible role

This role aims to bootstrap an empty zone into powerdns so that it can be
used immediately without needing to be created using powerdns-admin or
API calls.

For this, the contents of the SOA record, the zone name and it's type
need to be known, optionally the associated powerdns account.

## Configuration

A sample configuration is given below for setting up `demo.famedly.de`:

```yaml
- hosts: [dns_authoritative]
  roles:
    - name: powerdns-zone
      vars:
        powerdns_zone_name: demo.famedly.de
        powerdns_zone_type: "{{ 'MASTER' if 'dns_primary' in group_names else 'SLAVE' }}"
        # Assuming the primary has a variable called `ipv4`, store that ip in the
        # `master` column of the domain table of the secondaries
        powerdns_zone_master_ip: "{{ groups.dns_primary[0].ipv4 }}"
        powerdns_zone_account: famedlydemo
        powerdns_zone_soa_content: "ns0.famedly.de admin.famedly.de 2022010101 10800 3600 604800 3600"
        # Database configuration
        postgres_zone_database_type: postgres
        postgres_zone_database_user: pdns
        postgres_zone_database_password: asdoifjqwiejüojsdvinoöioeawjsf
        postgres_zone_database_name: pdns
        postgres_zone_database_host: 127.0.0.1
```
