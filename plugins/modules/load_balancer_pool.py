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
short_description: Manages load balancers on the cloudscale.ch IaaS service
description:
  - List, create, update, delete load balancers on the cloudscale.ch IaaS service.
  - List, create, update, delete pools on the cloudscale.ch IaaS service.
  - List, create, update, delete pool members on the cloudscale.ch IaaS service.
  - List, create, update, delete load balancer listeners on the cloudscale.ch IaaS service.
  - List, create, update, delete load balancer health monitors on the cloudscale.ch IaaS service.
notes:
  - If I(uuid) option is provided, it takes precedence over I(name) for load balancer selection. This allows to update the load balancers's name.
  - If no I(uuid) option is provided, I(name) is used for load balancer selection. If more than one load balancer with this name exists, execution is aborted.
author:
  - Gaudenz Steinlin (@gaudenz)
  - Kenneth Joss (@k-304)
version_added: "2.3.0"
options:
  state:
    description:
      - State of the load balancer pool.
    choices: [ running, absent ]
    default: running
    type: str
  name:
    description:
      - Name of the load balancer pool.
    type: str
  load_balancer:
    description:
      - UUID of the load balancer for this pool.
    type: str
  algorithm:
    description:
      - The algorithm according to which the incoming traffic is distributed between the pool members.
      - Currently the following algorithms are supported: I(round_robin), I(least_connections), I(source_ip).
    type: str
  protocol:
    description:
      - The protocol used for traffic between the load balancer and the pool members.
      - Currently the following protocols are supported: I(tcp), I(proxy), I(proxyv2).
  tags:
    description:
      - Tags assosiated with the load balancer. Set this to C({}) to clear any tags.
    type: dict
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = '''

'''

RETURN = '''

'''

from datetime import datetime, timedelta
from time import sleep
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)

ALLOWED_STATES = ('present',
                  'absent',
                  )
ALLOWED_POOL_ALGORITHMUS = ('round_robin',
                            'least_connections',
                            'source_ip',
                            )
ALLOWED_POOL_PROTOCOLS = ('tcp',
                          'proxy',
                          'proxyv2',
                          )


class AnsibleCloudscaleLoadBalancerPool(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleLoadBalancerPool, self).__init__(module)

        # Initialize load balancer dictionary
        self._info = {}

    # Init
    def _init_load_balancer_pool_container(self):
        return {
            'uuid': self._module.params.get('uuid') or self._info.get('uuid'),
            'name': self._module.params.get('name') or self._info.get('name'),
            'state': 'absent',
        }

    # Get a LB pool by name/uuid
    def _get_load_balancer_pool_info(self, refresh=False):
        if self._info and not refresh:
            return self._info
        self._info = self._init_load_balancer_pool_container()

        uuid = self._info.get('uuid')
        if uuid is not None:
            load_balancer_pool_info = self._get('load-balancers/pools/%s' % uuid)
            if load_balancer_pool_info:
                self._info = self._transform_state(load_balancer_pool_info)

        else:
            name = self._info.get('name')
            if name is not None:
                load_balancer_pools = self._get('load-balancers/pools') or []
                matching_load_balancer_pool = []
                for load_balancer_pool in load_balancer_pools:
                    if load_balancer_pool['name'] == name:
                        matching_load_balancer_pool.append(load_balancer_pool)

                if len(matching_load_balancer_pool) == 1:
                    self._info = self._transform_state(matching_load_balancer_pool[0])
                elif len(matching_load_balancer_pool) > 1:
                    self._module.fail_json(msg="More than one load balancer with name '%s' exists. "
                                           "Use the 'uuid' parameter to identify the load balancer." % name)

        return self._info

    @staticmethod
    def _transform_state(load_balancer_pool):
        if 'created_at' in load_balancer_pool:
            load_balancer_pool['state'] = 'present'
        else:
            load_balancer_pool['state'] = 'absent'
        return load_balancer_pool

    # Create LB Pool
    def _create_load_balancer_pool(self, load_balancer_pool_info):
        self._result['changed'] = True

        data = deepcopy(self._module.params)
        for i in ('state', 'api_timeout', 'api_token', 'api_url'):
            del data[i]

        self._result['diff']['before'] = self._init_load_balancer_pool_container()
        self._result['diff']['after'] = deepcopy(data)
        if not self._module.check_mode:
            self._post('load-balancers/pools', data)
            #load_balancer_pool_info = self._wait_for_state(('running', ))
            load_balancer_pool_info = self._wait_for_state()
        return load_balancer_pool_info

    # Wait for LB Pool to be up
    #def _wait_for_state(self, states):
    def _wait_for_state(self):
        start = datetime.now()
        timeout = self._module.params['api_timeout'] * 2
        while datetime.now() - start < timedelta(seconds=timeout):
            load_balancer_pool_info = self._get_load_balancer_pool_info(refresh=True)
            #if load_balancer_info.get('state') in states:
            if load_balancer_pool_info.get('created_at') is not None:
                return load_balancer_pool_info
            sleep(1)

        # Timeout succeeded
        if load_balancer_pool_info.get('name') is not None:
            msg = "Timeout while waiting for a state change on load balancer %s to states %s. " \
                  "Current state is %s." % (load_balancer_pool_info.get('name'), states, load_balancer_pool_info.get('state'))
        else:
            name_uuid = self._module.params.get('name') or self._module.params.get('uuid')
            msg = 'Timeout while waiting to find the load balancer %s' % name_uuid

        self._module.fail_json(msg=msg)

    # Update LB Pool
    def _update_load_balancer_pool(self, load_balancer_pool_info):

        previous_state = load_balancer_pool_info.get('state')

        load_balancer_pool_info = self._update_param('name', load_balancer_pool_info)
        load_balancer_pool_info = self._update_param('tags', load_balancer_pool_info)

        return load_balancer_pool_info

    # Update LB Pool parameters
    def _update_param(self, param_key, load_balancer_pool_info, requires_stop=False):
        param_value = self._module.params.get(param_key)
        if param_value is None:
            return load_balancer_pool_info

        if 'slug' in load_balancer_pool_info[param_key]:
            load_balancer_pool_v = load_balancer_pool_info[param_key]['slug']
        else:
            load_balancer_pool_v = load_balancer_pool_info[param_key]

        if load_balancer_pool_v != param_value:
            # Set the diff output
            self._result['diff']['before'].update({param_key: load_balancer_pool_v})
            self._result['diff']['after'].update({param_key: param_value})

            self._result['changed'] = True
            if not self._module.check_mode:
                patch_data = {
                    param_key: param_value,
                }

                # Response is 204: No Content
                self._patch('load-balancers/pools/%s' % load_balancer_pool_info['uuid'], patch_data)

        return load_balancer_pool_info

    def present_load_balancer_pool(self):
        load_balancer_pool_info = self._get_load_balancer_pool_info()

        if load_balancer_pool_info.get('state') != "absent":
            load_balancer_pool_info = self._update_load_balancer_pool(load_balancer_pool_info)
        else:
            load_balancer_pool_info = self._create_load_balancer_pool(load_balancer_pool_info)

        return load_balancer_pool_info

    # Modul state is present
    def absent_load_balancer_pool(self):
        load_balancer_pool_info = self._get_load_balancer_pool_info()
        if load_balancer_pool_info.get('state') != "absent":
            self._result['changed'] = True
            self._result['diff']['before'] = deepcopy(load_balancer_pool_info)
            self._result['diff']['after'] = self._init_load_balancer_pool_container()
            if not self._module.check_mode:
                self._delete('load-balancers/pools/%s' % load_balancer_pool_info['uuid'])
                load_balancer_pool_info = self._wait_for_state(('absent', ))
        return load_balancer_pool_info


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=ALLOWED_STATES),
        name=dict(),
        uuid=dict(),
        load_balancer=dict(),
        algorithm=dict(choices=ALLOWED_POOL_ALGORITHMUS),
        protocol=dict(choices=ALLOWED_POOL_PROTOCOLS),
        tags=dict(type='dict'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(),
        required_one_of=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    cloudscale_load_balancer_pool = AnsibleCloudscaleLoadBalancerPool(module)
    if module.params['state'] == "absent":
        load_balancer_pool = cloudscale_load_balancer_pool.absent_load_balancer_pool()
    else:
        load_balancer_pool = cloudscale_load_balancer_pool.present_load_balancer_pool()

    result = cloudscale_load_balancer_pool.get_result(load_balancer_pool)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
