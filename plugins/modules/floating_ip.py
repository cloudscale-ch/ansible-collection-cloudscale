#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: floating_ip
short_description: Manages floating IPs on the cloudscale.ch IaaS service
description:
  - Create, assign and delete floating IPs on the cloudscale.ch IaaS service.
notes:
  - Once a floating_ip is created all parameters except C(server) and C(tags) are read-only.
  - This module requires the ipaddress python library. This library is included in Python since version 3.3. It is available as a
    module on PyPI for earlier versions.
author:
  - Gaudenz Steinlin (@gaudenz)
  - Denis Krienbühl (@href)
  - René Moser (@resmo)
version_added: 1.0.0
options:
  ip:
    description:
      - Floating IP address to change.
      - One of C(ip) or C(name) is required to identify the floating IP.
    aliases: [ network ]
    type: str
  name:
    description:
      - Name to identifiy the floating IP address.
      - One of C(ip) or C(name) is required to identify the floating IP.
    aliases: [ network ]
    version_added: 2.0.0
    type: str
  state:
    description:
      - State of the floating IP.
    default: present
    choices: [ present, absent ]
    type: str
  ip_version:
    description:
      - IP protocol version of the floating IP.
    choices: [ 4, 6 ]
    type: int
  server:
    description:
      - UUID of the server assigned to this floating IP.
    type: str
  type:
    description:
      - The type of the floating IP.
    choices: [ regional, global ]
    type: str
    default: regional
  region:
    description:
      - Region in which the floating IP resides (e.g. C(lgp) or C(rma)).
        If omitted, the region of the project default zone is used.
        This parameter must be omitted if I(type) is set to C(global).
    type: str
  prefix_length:
    description:
      - Only valid if I(ip_version) is 6.
      - Prefix length for the IPv6 network. Currently only a prefix of /56 can be requested. If no I(prefix_length) is present, a
        single address is created.
    choices: [ 56 ]
    type: int
  reverse_ptr:
    description:
      - Reverse PTR entry for this address.
      - You cannot set a reverse PTR entry for IPv6 floating networks. Reverse PTR entries are only allowed for single addresses.
    type: str
  tags:
    description:
      - Tags associated with the floating IP. Set this to C({}) to clear any tags.
    type: dict
    version_added: 1.1.0
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = '''
# Request a new floating IP without assignment to a server
- name: Request a floating IP
  cloudscale_ch.cloud.floating_ip:
    name: IP to my server
    ip_version: 4
    reverse_ptr: my-server.example.com
    api_token: xxxxxx

# Request a new floating IP with assignment
- name: Request a floating IP
  cloudscale_ch.cloud.floating_ip:
    name: web
    ip_version: 4
    server: 47cec963-fcd2-482f-bdb6-24461b2d47b1
    reverse_ptr: my-server.example.com
    api_token: xxxxxx

# Assign an existing floating IP to a different server by its IP address
- name: Move floating IP to backup server
  cloudscale_ch.cloud.floating_ip:
    ip: 192.0.2.123
    server: ea3b39a3-77a8-4d0b-881d-0bb00a1e7f48
    api_token: xxxxxx

# Assign an existing floating IP to a different server by name
- name: Move floating IP to backup server
  cloudscale_ch.cloud.floating_ip:
    name: IP to my server
    server: ea3b39a3-77a8-4d0b-881d-0bb00a1e7f48
    api_token: xxxxxx

# Request a new floating IPv6 network
- name: Request a floating IP
  cloudscale_ch.cloud.floating_ip:
    ip_version: 6
    prefix_length: 56
    server: 47cec963-fcd2-482f-bdb6-24461b2d47b1
    api_token: xxxxxx
    region: lpg1

# Assign an existing floating network to a different server
- name: Move floating IP to backup server
  cloudscale_ch.cloud.floating_ip:
    ip: '{{ floating_ip.network | ip }}'
    server: ea3b39a3-77a8-4d0b-881d-0bb00a1e7f48
    api_token: xxxxxx

# Release a floating IP
- name: Release floating IP
  cloudscale_ch.cloud.floating_ip:
    ip: 192.0.2.123
    state: absent
    api_token: xxxxxx
'''

RETURN = '''
name:
  description: The name of the floating ip
  returned: success when state == present
  type: str
  sample: my floating ip
  version_added: 2.0.0
href:
  description: The API URL to get details about this floating IP.
  returned: success when state == present
  type: str
  sample: https://api.cloudscale.ch/v1/floating-ips/2001:db8::cafe
network:
  description: The CIDR notation of the network that is routed to your server.
  returned: success when state == present
  type: str
  sample: 2001:db8::cafe/128
next_hop:
  description: Your floating IP is routed to this IP address.
  returned: success when state == present
  type: str
  sample: 2001:db8:dead:beef::42
reverse_ptr:
  description: The reverse pointer for this floating IP address.
  returned: success when state == present
  type: str
  sample: 185-98-122-176.cust.cloudscale.ch
server:
  description: The floating IP is routed to this server.
  returned: success when state == present
  type: str
  sample: 47cec963-fcd2-482f-bdb6-24461b2d47b1
ip:
  description: The floating IP address or network. This is always present and used to identify floating IPs after creation.
  returned: success
  type: str
  sample: 185.98.122.176
region:
  description: The region of the floating IP.
  returned: success when state == present
  type: dict
  sample: {'slug': 'lpg'}
state:
  description: The current status of the floating IP.
  returned: success
  type: str
  sample: present
tags:
  description: Tags assosiated with the floating IP.
  returned: success
  type: dict
  sample: { 'project': 'my project' }
  version_added: 1.1.0
'''

import traceback

IPADDRESS_IMP_ERR = None
try:
    from ipaddress import ip_network
    HAS_IPADDRESS = True
except ImportError:
    IPADDRESS_IMP_ERR = traceback.format_exc()
    HAS_IPADDRESS = False

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)


class AnsibleCloudscaleFloatingIp(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleFloatingIp, self).__init__(
            module=module,
            resource_key_uuid='ip',
            resource_name='floating-ips',
            resource_create_param_keys=[
                'ip_version',
                'server',
                'prefix_length',
                'reverse_ptr',
                'type',
                'region',
                'tags',
            ],
            resource_update_param_keys=[
                'server',
                'tags',
            ],
        )

        self.name_tag = "ansible_name"

    def query(self):
        # Initialize
        self._resource_data = self.init_resource()

        # Query by UUID
        uuid = self._module.params[self.resource_key_uuid]
        if uuid is not None:
            resource = self._get('%s/%s' % (self.resource_name, uuid))
            if resource:
                self._resource_data = resource
                self._resource_data['state'] = "present"

        else:
            # Floating IP API has no name field, querying by the a custom tag used as name
            name = self._module.params[self.resource_key_name]
            resources = self._get('%s?tag:%s=%s' % (self.resource_name, self.name_tag, name))
            if resources:
                # Fail on more than one resource with identical name
                if len(resources) > 1:
                    self._module.fail_json(
                        msg="More than one %s resource with '%s' exists: %s. "
                            "Use the '%s' parameter to identify the resource." % (
                                self.resource_name,
                                self.resource_key_name,
                                name,
                                self.resource_key_uuid
                            )
                    )
                elif len(resources) == 1:
                    self._resource_data = resources[0]
                    self._resource_data['state'] = "present"

        return self._resource_data

    def _append_name_tag(self):
        # Append name to the tags to handle idempotency
        self._module.params['tags'] = self._module.params['tags'] or dict()
        self._module.params['tags'].update({
            self.name_tag: self._module.params[self.resource_key_name],
        })

    def create(self, resource):
        # Fail when missing params for creation
        self._module.fail_on_missing_params([self.resource_key_name])

        # Append name to the tags to handle idempotency
        self._append_name_tag()
        return super(AnsibleCloudscaleFloatingIp, self).create(resource)

    def update(self, resource):
        # Append name to the tags to handle idempotency
        self._append_name_tag()
        return super(AnsibleCloudscaleFloatingIp, self).update(resource)

    def get_result(self, resource):
        if resource:
            for k, v in resource.items():
                self._result[k] = v

            # Transform the name tag back to a name field
            if 'name' not in self._result:
                self._result['name'] = self._result.get('tags', dict()).pop(self.name_tag, '')
        return self._result

def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str'),
        state=dict(default='present', choices=('present', 'absent'), type='str'),
        ip=dict(aliases=('network',), type='str'),
        ip_version=dict(choices=(4, 6), type='int'),
        server=dict(type='str'),
        type=dict(type='str', choices=('regional', 'global'), default='regional'),
        region=dict(type='str'),
        prefix_length=dict(choices=(56,), type='int'),
        reverse_ptr=dict(type='str'),
        tags=dict(type='dict'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('ip', 'name'),),
        supports_check_mode=True,
    )

    if not HAS_IPADDRESS:
        module.fail_json(msg=missing_required_lib('ipaddress'), exception=IPADDRESS_IMP_ERR)

    cloudscale_floating_ip = AnsibleCloudscaleFloatingIp(module)

    if module.params['state'] == 'absent':
        result = cloudscale_floating_ip.absent()
    else:
        result = cloudscale_floating_ip.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
