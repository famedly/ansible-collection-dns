# `famedly.dns.powerdns-account` ansible role

This role can be used for configuring powerdns accounts in powerdns-admin,
setting description, contact and mail contact on an account, enabling you
to automatically create empty accounts in powerdns-admin which can be used
with powerdns.

## Usage

An example is given below for a list of dicts in a variable called `accounts`:

```yaml
- include_role:
    name: powerdns-account
  vars:
    powerdns_account_slug: "{{ account.slug }}"
    powerdns_account_description: "{{ account.description }}"
    powerdns_account_contact_person: "{{ account.contact_person }}"
    powerdns_account_contact_email: "{{ account.contact_email }}"
    # Database configuration
    powerdns_account_database_type: postgres
    powerdns_account_database_user: pdns-admin
    powerdns_account_database_password: dsjfaoiwnafvuawqidöq
    powerdns_account_database_name: pdns-admin
    powerdns_account_database_host: 127.0.0.1
  loop: "{{ accounts }}"
  loop_control:
    loop_var: account
    label: "{{ acount.slug }}"
```

The `accounts` variable could be populated by data sources like LDAP,
other databases or arbitrary API calls returning this structure, enabling
automated acount management in powerdns-admin.

## Planned features

- User management: users can be associated with accounts, but given that
  only users who have logged in atleast once can be used, this is not yet
  implemented.

- Allow deletion of an account if all zones of the account have been removed,
  optionally force deletion of the account (leaving orphan zones in powerdns behind).
