#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2026, cloudscale.ch AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: interface
short_description: Manages network interfaces on the cloudscale.ch IaaS service
description:
  - Create and remove network interfaces attached to routers.
author:
  - Michael Weibel (@mweibel)
version_added: "2.6.0"
notes:
  - B(Updates are not supported.) Changing any parameter requires deleting and recreating the interface.
options:
  router:
    description:
      - UUID of the router to attach the interface to.
    type: str
    required: true
  network:
    description:
      - UUID of the network to attach.
      - Used as the idempotency key to identify the interface within the router.
    type: str
    required: true
  addresses:
    description:
      - List of address configurations for the interface.
      - Required when I(state=present).
    type: list
    elements: dict
    suboptions:
      subnet:
        description:
          - UUID of the subnet.
        type: str
        required: true
      address:
        description:
          - The IP address to assign.
        type: str
        required: true
  state:
    description:
      - State of the interface.
    choices: [ present, absent ]
    default: present
    type: str
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = '''
---
- name: Ensure router exists
  cloudscale_ch.cloud.router:
    name: "{{ resource_prefix }}-router"
    zone: "{{ cloudscale_zone }}"
    internet_gateway: false
  register: router

- name: Attach a network interface with a specific IP address
  cloudscale_ch.cloud.interface:
    router: '{{ router.uuid }}'
    network: '{{ network.uuid }}'
    addresses:
      - subnet: '{{ subnet.uuid }}'
        address: '172.16.0.1'
    api_token: xxxxxx

- name: Remove a network interface from a router
  cloudscale_ch.cloud.interface:
    router: '{{ router.uuid }}'
    network: '{{ network.uuid }}'
    state: absent
    api_token: xxxxxx
'''

RETURN = '''
---
uuid:
  description: The unique identifier for the interface.
  returned: success when not state == absent
  type: str
  sample: cfde831a-4e87-4a75-960f-89b0148aa2cc
network:
  description: The network this interface is attached to.
  returned: success when not state == absent
  type: complex
  contains:
    href:
      description: API URL to get details about the network.
      returned: success
      type: str
      sample: https://api.cloudscale.ch/v1/networks/33333333-1864-4608-853a-0771b6885a3
    uuid:
      description: The unique identifier for the network.
      returned: success
      type: str
      sample: 33333333-1864-4608-853a-0771b6885a3
    name:
      description: The name of the network.
      returned: success
      type: str
      sample: my-network
addresses:
  description: List of address objects assigned to this interface.
  returned: success when not state == absent
  type: complex
  contains:
    address:
      description: The IP address assigned to the interface.
      returned: success
      type: str
      sample: 172.16.0.1
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
          sample: https://api.cloudscale.ch/v1/subnets/33333333-1864-4608-853a-0771b6885a3
        uuid:
          description: The unique identifier for the subnet.
          returned: success
          type: str
          sample: 33333333-1864-4608-853a-0771b6885a3
        cidr:
          description: The CIDR of the subnet.
          returned: success
          type: str
          sample: 172.16.0.0/24
type:
  description: The type of the interface (e.g. C(private)).
  returned: success when not state == absent
  type: str
  sample: private
mac_address:
  description: The MAC address of the interface.
  returned: success when not state == absent
  type: str
  sample: fa:16:3e:b9:2c:8a
state:
  description: State of the interface.
  returned: success
  type: str
  sample: present
'''

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)


class AnsibleCloudscaleInterface(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleInterface, self).__init__(
            module,
            resource_name='routers/%s/interfaces' % module.params['router'],
            resource_create_param_keys=[
                'network',
                'addresses',
            ],
            resource_update_param_keys=[
                'addresses',
            ],
        )

    def update(self, resource):
        # The interface API has no update endpoint.
        # Any change to a create parameter requires delete+recreate.
        if self.has_differences(resource):
            self._module.fail_json(
                msg="Updating interfaces is not supported. "
                    "Use state=absent followed by state=present to recreate.",
            )
        return resource

    def find_difference(self, key, resource, param):
        # Address objects carry extra fields (version, reverse_ptr, subnet as
        # a stub dict), so compare only the requested (address, subnet uuid) pairs.
        if key == 'addresses':
            live = {
                (a.get('address'), (a.get('subnet') or {}).get('uuid'))
                for a in (resource.get('addresses') or [])
            }
            want = {(a.get('address'), a.get('subnet')) for a in (param or [])}
            return live != want
        return super().find_difference(key, resource, param)

    def query(self):
        self._resource_data = self.init_resource()

        # Interfaces are not queryable on their own. The only way to read them
        # is to fetch the associated router and go through its interfaces array.
        # The network is used as the idempotency key within the router.
        router = self._get('routers/%s' % self._module.params['router'])
        interfaces = (router or {}).get('interfaces') or []

        network = self._module.params['network']
        for interface in interfaces:
            if interface.get('network', {}).get('uuid') == network:
                self._resource_data = interface
                self._resource_data['state'] = 'present'
                break

        return self.pre_transform(self._resource_data)

    def delete_resource(self, resource):
        # Interfaces are embedded in the router and never carry their own 'href',
        # so delete via the nested collection path.
        href = '%s/%s' % (self.resource_name, resource['uuid'])
        self._delete(href)

    def absent(self):
        resource = self.query()
        if resource['state'] != 'absent':
            self._result['changed'] = True
            self._result['diff']['before'] = deepcopy(resource)
            self._result['diff']['after'] = self.init_resource()

            if not self._module.check_mode:
                self.delete_resource(resource)
                resource['state'] = 'absent'
        return self.get_result(resource)


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        router=dict(type='str', required=True),
        network=dict(type='str', required=True),
        addresses=dict(
            type='list',
            elements='dict',
            options=dict(
                subnet=dict(type='str', required=True),
                address=dict(type='str', required=True),
            ),
        ),
        state=dict(default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=(('state', 'present', ('addresses',)),),
        supports_check_mode=True,
    )

    cloudscale_interface = AnsibleCloudscaleInterface(module)

    if module.params['state'] == 'absent':
        result = cloudscale_interface.absent()
    else:
        result = cloudscale_interface.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
