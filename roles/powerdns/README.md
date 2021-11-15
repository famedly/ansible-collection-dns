# `famedly.local.powerdns`

## Overview

## Configuration

## Updating the role

- When the version is bumped, the default postgres schema in `files/schema.pgsql.sql`
  must be updated aswell, the file is not packaged in alpine per default, so the
  upstream source repo should be used:
  https://github.com/PowerDNS/pdns/blob/rel/auth-4.5.x/modules/gpgsqlbackend/schema.pgsql.sql
