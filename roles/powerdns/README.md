# `famedly.dns.powerdns` ansible collection

## Overview

## Configuration

Most configuration options from
[PowerDNSs' Authoritative Server Settings](https://doc.powerdns.com/authoritative/settings.html)
are available by setting `powerdns_config_$option`, where
`$option` is written in `snake_case`.

### Dynamic record types

#### `ALIAS` records

To enable `ALIAS` records (think: `CNAME` but allowed at zone apex),
set the following configuration options:
```yaml
# This turns on ALIAS processing, otherwise `NODATA` is returned for the record
powerdns_config_expand_alias: true
# Configure the DNS server to query for the content of the ALIAS record,
# if this is not set, ALIAS records will not be available
powerdns_config_resolver: 9.9.9.9:53
# If using DNSSEC without live-signing, the primary will query the content
# and sign it before sending it in the AXFR
powerdns_config_outgoing_axfr_expand_alias: true
```

For more operational instructions on `ALIAS` records, see
[PowerDNSs' documentation on `ALIAS` records](https://doc.powerdns.com/authoritative/guides/alias.html)

#### `DNAME` records

Not enabled per default, set `powerdns_config_dname_processing: true`.

#### `LUA` records

To enable [`LUA` records](https://doc.powerdns.com/authoritative/lua-records/index.html),
set `powerdns_config_enable_lua_records` to `true` or `'shared'`.

### Automating DNSSEC Delegation Trust Maintenance (RFC7344)

[RFC7344](https://datatracker.ietf.org/doc/html/rfc7344.html) specifies
how to automatically publish DNS Key signing keys (KSKs) using DNS itself.

To enable this behaviour, configure the following:
```yaml
powerdns_config_default_publish_cdnskey: 1
powerdns_config_default_publish_cds: 1,2,4
# sha1, sha256, sha384 as per http://www.iana.org/assignments/ds-rr-types/ds-rr-types.xhtml#ds-rr-types-1
```
It is also possible to configure this per-zone, allowing to control
the used signing algorithms for each zone. Set the zone metadata accordingly:
```
PUBLISH-CDNSKEY: 1 # true
PUBLISH-CDS: 1,2 # sha1, sha256
```

## Updating the role

- When the version is bumped, the default postgres schema in `files/schema.pgsql.sql`
  must be updated aswell, the file is not packaged in alpine per default, so the
  upstream source repo should be used:
  https://github.com/PowerDNS/pdns/blob/rel/auth-4.5.x/modules/gpgsqlbackend/schema.pgsql.sql
