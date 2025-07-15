# `famedly.dns.powerdns-admin` ansible role

Deploys a containerized instance of [powerdns-admin](https://github.com/PowerDNS-Admin/PowerDNS-Admin),
a fully featured web interface for powerdns with various supported auth
methods and fine-grained user access management.

## Configuration

This role sets up powerdns-admin with a postgres database, using other
databases (including the default sqlite) is currently not supported.
Configuring the database is done like this:

```yaml
powerdns_admin_database_type: postgresql
powerdns_admin_database_user: pdns-admin
powerdns_admin_database_password: your_password_here
powerdns_admin_database_name: pdns-admin
powerdns_admin_database_socket: 127.0.0.1
```

Configuring the connection to powerdns using it's API:

```yaml
powerdns_admin_api_url: http://powerdns:8081/
powerdns_admin_api_key: my_api_key_here
powerdns_admin_api_version: powerdns_version_here
```

Configuring which authentications should be en- or
disabled, and wether local open signup should be enabled.
```yaml
powerdns_admin_auth_local_enabled: true|false
powerdns_admin_ldap_enabled: true|false

# Enable local signup?
powerdns_admin_auth_local_signup_enabled: false
```

### LDAP configuration

```yaml
powerdns_admin_ldap_type: ldap|ad
powerdns_admin_ldap_uri: "ldap://localhost"
powerdns_admin_ldap_base_dn: dc=my,dc=organization,dc=net
powerdns_admin_ldap_bind_user: ldap_read_user
powerdns_admin_ldap_bind_password: ldap_read_user_password
```

For all options, see `powerdns_admin_ldap_*` in [`defaults/main.yml`](./defaults/main.yml).
