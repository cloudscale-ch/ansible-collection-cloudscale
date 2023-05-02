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
  - List, create, update, delete pool members on the cloudscale.ch IaaS service.
notes:
  - If I(uuid) option is provided, it takes precedence over I(name) for pool member selection. This allows to update the load balancers's name.
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
    default: running
    type: str
  name:


  load_balancer_pool:
    description:
      - UUID of the load balancer pool.
    type: str


'''

EXAMPLES = '''

'''

RETURN = '''

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
ALLOWED_ENABLED = ('true',
                   'false',
                   )


class AnsibleCloudscaleLoadBalancerPoolMember(AnsibleCloudscaleBase):

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
        enabled=dict(default='true', choices=ALLOWED_ENABLED),
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

    cloudscale_load_balancer_pool_member = AnsibleCloudscaleLoadBalancerPoolMember(
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
    cloudscale_load_balancer_pool_member.query_constraint_keys = []

    if module.params['state'] == "absent":
        result = cloudscale_load_balancer_pool_member.absent()
    else:
        result = cloudscale_load_balancer_pool_member.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
