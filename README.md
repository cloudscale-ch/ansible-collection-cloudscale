
![Collection Integration tests](https://github.com/cloudscale-ch/ansible-collection-cloudscale/workflows/Collection%20Integration%20tests/badge.svg)
[![Codecov](https://img.shields.io/codecov/c/github/cloudscale-ch/ansible-collection-cloudscale)](https://codecov.io/gh/cloudscale-ch/ansible-collection-cloudscale)
[![License](https://img.shields.io/badge/license-GPL%20v3.0-brightgreen.svg)](LICENSE)

# Ansible Collection for cloudscale.ch Cloud

This collection provides a series of Ansible modules and plugins for interacting with the [cloudscale.ch](https://www.cloudscale.ch) Cloud.

## Requirements

- ansible version >= 2.9

## Installation

To install the collection hosted in Galaxy:

```bash
ansible-galaxy collection install cloudscale_ch.cloud
```

To upgrade to the latest version of the collection:

```bash
ansible-galaxy collection install cloudscale_ch.cloud --force
```

## Usage

### Playbooks

To use a module from cloudscale.ch collection, please reference the full namespace, collection name, and modules name that you want to use:

```yaml
---
- name: Using cloudscale.ch collection
  hosts: localhost
  tasks:
    - cloudscale_ch.cloud.server:
        name: web1
        image: debian-10
        flavor: flex-2
        ssh_keys: ssh-rsa XXXXXXXXXX...XXXX ansible@cloudscale
        server_groups: web-group
        zone: lpg1
        api_token: ...
```

Or you can add full namepsace and collection name in the `collections` element:

```yaml
---
- name: Using cloudscale.ch collection
  hosts: localhost
  collections:
    - cloudscale_ch.cloud
  tasks:
    - server:
        name: web1
        image: debian-10
        flavor: flex-2
        ssh_keys: ssh-rsa XXXXXXXXXX...XXXX ansible@cloudscale
        server_groups: web-group
        zone: lpg1
        api_token: ...
```

### Roles

For existing Ansible roles, please also reference the full namespace, collection name, and modules name which used in tasks instead of just modules name.

### Plugins

To use a pluign, please reference the full namespace, collection name, and plugins name that you want to use:

```yaml
plugin: cloudscale_ch.cloud.<myplugin>
```

## Contributing

There are many ways in which you can participate in the project, for example:

- Submit bugs and feature requests, and help us verify as they are checked in
- Review source code changes
- Review the documentation and make pull requests for anything from typos to new content
- If you are interested in fixing issues and contributing directly to the code base, please see the [CONTRIBUTING](CONTRIBUTING.md) document.

## License

GNU General Public License v3.0

See [COPYING](COPYING) to see the full text.
