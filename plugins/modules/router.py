#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2026, cloudscale.ch AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: router
short_description: Manages routers on the cloudscale.ch IaaS service
description:
  - Create and remove routers.
author:
  - Michael Weibel (@mweibel)
version_added: "2.6.0"
notes:
  - B(Updates are not supported.) Changing any parameter requires deleting and recreating the router.
options:
  name:
    description:
      - Name of the router.
      - Either I(name) or I(uuid) is required.
    type: str
  uuid:
    description:
      - UUID of the router.
      - Either I(name) or I(uuid) is required.
    type: str
  zone:
    description:
      - Zone slug of the router (e.g. C(lpg1) or C(rma1)).
    type: str
  internet_gateway:
    description:
      - Whether this router acts as an internet gateway.
    default: false
    type: bool
  tags:
    description:
      - Tags associated with the router. Set this to C({}) to clear any tags.
    type: dict
  state:
    description:
      - State of the router.
    choices: [ present, absent ]
    default: present
    type: str
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = '''
---
- name: Ensure a router exists
  cloudscale_ch.cloud.router:
    name: my-router
    zone: lpg1
    api_token: xxxxxx

- name: Ensure a router with internet gateway exists
  cloudscale_ch.cloud.router:
    name: my-internet-gateway
    zone: lpg1
    internet_gateway: true
    api_token: xxxxxx

- name: Ensure a router is absent
  cloudscale_ch.cloud.router:
    name: my-router
    state: absent
    api_token: xxxxxx
'''

RETURN = '''
---
href:
  description: API URL to get details about this router.
  returned: success
  type: str
  sample: https://api.cloudscale.ch/v1/routers/cfde831a-4e87-4a75-960f-89b0148aa2cc
uuid:
  description: The unique identifier for the router.
  returned: success
  type: str
  sample: cfde831a-4e87-4a75-960f-89b0148aa2cc
name:
  description: The name of the router.
  returned: success
  type: str
  sample: my-router
created_at:
  description: The creation date and time of the router.
  returned: success
  type: str
  sample: "2025-01-01T13:18:42.511407Z"
status:
  description: The status of the router.
  returned: success
  type: str
  sample: active
zone:
  description: The zone of the router.
  returned: success
  type: dict
  sample: { 'slug': 'lpg1' }
internet_gateway:
  description: Whether this router acts as an internet gateway.
  returned: success
  type: bool
  sample: false
internet_gateway_addresses:
  description: List of internet gateway address objects (populated when I(internet_gateway) is C(true)).
  returned: success
  type: complex
  contains:
    address:
      description: The internet gateway IP address.
      returned: success
      type: str
      sample: 100.112.2.182
    version:
      description: The IP version of the address (C(4) or C(6)).
      returned: success
      type: int
      sample: 4
    reverse_ptr:
      description: The reverse DNS pointer (PTR) for the address.
      returned: success
      type: str
      sample: 185-98-122-176.cust.cloudscale.ch
    subnet:
      description: The subnet the address belongs to.
      returned: success
      type: complex
      contains:
        href:
          description: API URL to get details about the subnet.
          returned: success
          type: str
          sample: https://api.cloudscale.ch/v1/subnets/67b4bb7b-e595-4485-98e3-e48f5e1fae66
        uuid:
          description: The unique identifier for the subnet.
          returned: success
          type: str
          sample: 67b4bb7b-e595-4485-98e3-e48f5e1fae66
        cidr:
          description: The CIDR of the subnet.
          returned: success
          type: str
          sample: 172.16.0.0/24
interfaces:
  description: List of interface objects attached to this router.
  returned: success
  type: complex
  contains:
    uuid:
      description: The unique identifier for the interface.
      returned: success
      type: str
      sample: baeac2cc-94fd-4913-b7a5-d0e811f3e1ce
    type:
      description: The type of the interface (e.g. C(private)).
      returned: success
      type: str
      sample: private
    mac_address:
      description: The MAC address of the interface.
      returned: success
      type: str
      sample: fa:16:3e:67:31:6e
    network:
      description: The network this interface is attached to.
      returned: success
      type: complex
      contains:
        href:
          description: API URL to get details about the network.
          returned: success
          type: str
          sample: https://api.cloudscale.ch/v1/networks/5e346d59-b671-4236-99cc-10cf49e7d56d
        uuid:
          description: The unique identifier for the network.
          returned: success
          type: str
          sample: 5e346d59-b671-4236-99cc-10cf49e7d56d
        name:
          description: The name of the network.
          returned: success
          type: str
          sample: my-network
    addresses:
      description: List of address objects assigned to this interface.
      returned: success
      type: complex
      contains:
        address:
          description: The IP address assigned to the interface.
          returned: success
          type: str
          sample: 172.20.160.103
        version:
          description: The IP version of the address (C(4) or C(6)).
          returned: success
          type: int
          sample: 4
        reverse_ptr:
          description: The reverse DNS pointer (PTR) for the address.
          returned: success
          type: str
          sample: null
        subnet:
          description: The subnet the address belongs to.
          returned: success
          type: complex
          contains:
            href:
              description: API URL to get details about the subnet.
              returned: success
              type: str
              sample: https://api.cloudscale.ch/v1/subnets/9386e32c-4388-4709-a14e-0ec69ab9e354
            uuid:
              description: The unique identifier for the subnet.
              returned: success
              type: str
              sample: 9386e32c-4388-4709-a14e-0ec69ab9e354
            cidr:
              description: The CIDR of the subnet.
              returned: success
              type: str
              sample: 172.20.160.0/24
state:
  description: State of the router.
  returned: success
  type: str
  sample: present
tags:
  description: Tags associated with the router.
  returned: success
  type: dict
  sample: { 'project': 'my project' }
'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)


class AnsibleCloudscaleRouter(AnsibleCloudscaleBase):

    def update(self, resource):
        # The router API has no update endpoint.
        # Any change to a create parameter requires delete+recreate.
        if self.has_differences(resource):
            self._module.fail_json(
                msg="Updating routers is not supported. "
                    "Use state=absent followed by state=present to recreate.",
            )
        return resource

    def find_difference(self, key, resource, param):
        if key == 'zone':
            return resource.get('zone', {}).get('slug') != param
        return super().find_difference(key, resource, param)


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str'),
        uuid=dict(type='str'),
        zone=dict(type='str'),
        internet_gateway=dict(type='bool', default=False),
        tags=dict(type='dict'),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        required_if=(('state', 'present', ('name',),),),
        supports_check_mode=True,
    )

    cloudscale_router = AnsibleCloudscaleRouter(
        module,
        resource_name='routers',
        resource_create_param_keys=[
            'name',
            'zone',
            'internet_gateway',
            'tags',
        ],
        resource_update_param_keys=[
            'name',
            'internet_gateway',
            'tags',
        ],
    )

    cloudscale_router.query_constraint_keys = [
        'zone',
    ]

    if module.params['state'] == 'absent':
        result = cloudscale_router.absent()
    else:
        result = cloudscale_router.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
