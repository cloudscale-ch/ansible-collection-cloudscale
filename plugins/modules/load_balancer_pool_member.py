#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2023, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# Copyright: (c) 2023, Kenneth Joss <kenneth.joss@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: load_balancer
short_description: Manages load balancer pool members on the cloudscale.ch IaaS service
description:
  - Get, create, update, delete pool members on the cloudscale.ch IaaS service.
notes:
  - If I(uuid) option is provided, it takes precedence over I(name) for pool member selection. This allows to update the member's name.
  - If no I(uuid) option is provided, I(name) is used for pool member selection. If more than one load balancer with this name exists, execution is aborted.
author:
  - Gaudenz Steinlin (@gaudenz)
  - Kenneth Joss (@k-304)
version_added: "2.3.0"
options:
  state:
    description:
      - State of the load balancer pool member.
    choices: [ present, absent ]
    default: present
    type: str
  name:
    description:
      - Name of the load balancer pool member.
      - Either I(name) or I(uuid) are required.
    type: str
  uuid:
    description:
      - UUID of the load balancer.
      - Either I(name) or I(uuid) are required.
    type: str
  load_balancer_pool:
    description:
      - UUID of the load balancer pool.
    type: str
  enabled:
    description:
      - Pool member will not receive traffic if false. Default is true.
    default: true
    type: bool
  protocol_port:
    description:
      - The port to which actual traffic is sent.
    type: str
  monitor_port:
    description:
      - The port to which health monitor checks are sent.
      - If not specified, protocol_port will be used. Default is null.
    default: null
    type: str
  address:
    description:
      - The IP address to which traffic is sent.
    type: str
  subnet:
    description:
      - The subnet of the address must be specified here.
    type: str
  tags:
    description:
      - Tags assosiated with the load balancer. Set this to C({}) to clear any tags.
    type: dict
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = f'''
# Create a pool member for a load balancer pool using registered variables
- name: Create a load balancer pool
  cloudscale_ch.cloud.load_balancer_pool:
    name: 'swimming-pool'
    load_balancer: '514064c2-cfd4-4b0c-8a4b-c68c552ff84f'
    algorithm: 'round_robin'
    protocol: 'tcp'
    tags:
      project: ansible-test
      stage: production
      sla: 24-7
    api_token: xxxxxx
  register: load_balancer_pool

- name: Create a load balancer pool member
  cloudscale_ch.cloud.load_balancer_pool_member:
    name: 'my-shiny-swimming-pool-member'
    load_balancer_pool: '{{ load_balancer_pool.uuid }}'
    enabled: true
    protocol_port: '8080'
    monitor_port: '8081'
    subnet: '70d282ab-2a01-4abb-ada5-34e56a5a7eee'
    address: '172.16.0.100'
    tags:
      project: ansible-test
      stage: production
      sla: 24-7
    api_token: xxxxxx

# Get load balancer pool member facts by name
- name: Get facts of a load balancer pool member by name
  cloudscale_ch.cloud.load_balancer_pool_member:
    name: 'my-shiny-swimming-pool-member'
    api_token: xxxxxx
'''

RETURN = '''
href:
  description: API URL to get details about this load balancer
  returned: success when not state == absent
  type: str
  sample: https://api.cloudscale.ch/v1/load-balancers/pools/20a7eb11-3e17-4177-b46d-36e13b101d1c/members/b9991773-857d-47f6-b20b-0a03709529a9
uuid:
  description: The unique identifier for this load balancer pool member
  returned: success
  type: str
  sample: cfde831a-4e87-4a75-960f-89b0148aa2cc
name:
  description: The display name of the load balancer pool member
  returned: success
  type: str
  sample: web-lb-pool
enabled:
  description: THe status of the load balancer pool member
  returned: success
  type: bool
  sample: true
created_at:
  description: The creation date and time of the load balancer pool member
  returned: success when not state == absent
  type: datetime
  sample: 2023-02-07T15:32:02.308041Z
pool:
  description: The pool of the pool member
  returned: success
  type: dict
  sample: {
            "href": "https://api.cloudscale.ch/v1/load-balancers/pools/20a7eb11-3e17-4177-b46d-36e13b101d1c",
            "uuid": "20a7eb11-3e17-4177-b46d-36e13b101d1c",
            "name": "web-lb-pool"
            }
protocol_port:
  description: The port to which actual traffic is sent
  returned: success
  type: str
  sample: 8080
monitor_port:
  description: The port to which health monitor checks are sent
  returned: success
  type: str
  sample: 8081
address:
  description: The IP address to which traffic is sent
  returned: success
  type: str
  sample: 10.11.12.3
subnet:
  description: The subnet in a private network in which address is located
  returned: success
  type: dict
  sample: {
            "href": "https://api.cloudscale.ch/v1/subnets/70d282ab-2a01-4abb-ada5-34e56a5a7eee",
            "uuid": "70d282ab-2a01-4abb-ada5-34e56a5a7eee",
            "cidr": "10.11.12.0/24"
            }
monitor_status:
  description: The status of the pool's health monitor check for this member
  returned: success
  type: str
  sample: up
tags:
  description: Tags assosiated with the load balancer
  returned: success
  type: dict
  sample: { 'project': 'my project' }
'''

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)

ALLOWED_STATES = ('present',
                  'absent',
                  )


class AnsibleCloudscaleLoadBalancerPoolMember(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleLoadBalancerPoolMember, self).__init__(
            module,
            resource_name='load-balancers/pools/%s/members' % module.params['load_balancer_pool'],
            resource_create_param_keys=[
                'name',
                'load_balancer_pool',
                'enabled',
                'protocol_port',
                'monitor_port',
                'address',
                'subnet',
                'tags',
            ],
            resource_update_param_keys=[
                'name',
                'enabled',
                'tags',
            ],
        )

    def create(self, resource, data=None):
        super().create(resource, data)

        if not data:
            data = dict()
        data = AnsibleCloudscaleLoadBalancerPoolMember.remove_param(self, data)

        if not self._module.check_mode:
            resource = self.wait_for_state('enabled', ('true', 'false'))
        return resource, data

    def remove_param(self, data):
        for param in self.resource_create_param_keys:
            data[param] = self._module.params.get(param)
        return data


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(),
        uuid=dict(),
        load_balancer_pool=dict(),
        enabled=dict(type='bool', default=True),
        protocol_port=dict(),
        monitor_port=dict(),
        subnet=dict(),
        address=dict(),
        tags=dict(type='dict'),
        state=dict(default='present', choices=ALLOWED_STATES),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(),
        required_one_of=(('name', 'uuid'), 'load_balancer_pool'),
        required_if=(('state', 'present', ('name',),),),
        supports_check_mode=True,
    )

    cloudscale_load_balancer_pool_member = AnsibleCloudscaleLoadBalancerPoolMember(module)
    cloudscale_load_balancer_pool_member.query_constraint_keys = []

    if module.params['state'] == "absent":
        result = cloudscale_load_balancer_pool_member.absent()
    else:
        result = cloudscale_load_balancer_pool_member.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
