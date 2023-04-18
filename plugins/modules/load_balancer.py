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
version_added: "0.0.1"
options:
  name:
    description:
      - Name of the load balancer.
      - Either I(name) or I(uuid) are required.
    type: str
  uuid:
    description:
      - UUID of the load balancer.
      - Either I(name) or I(uuid) are required.
    type: str
  # .....
'''

EXAMPLES = '''
# Create and start a load balancer
- name: Start cloudscale.ch load balancer
  cloudscale_ch.cloud.load_balancer:
    name: my-shiny-cloudscale-load-balancer
    zone: lpg1
    flavor: lb-small
    vip_addresses:
      subnet:
        15e061ac-c98a-4a26-85df-b25d47801e99
      address:
        172.29.177.11
    tags:
      project: my project
    api_token: xxxxxx
# .....
'''

RETURN = '''
href:
  description: API URL to get details about this load balancer
  returned: success when not state == absent
  type: str
  sample: https://api.cloudscale.ch/v1/load-balancers/0f62e0a7-f459-4fc4-9c25-9e57b6cb4b2f
'''

from datetime import datetime, timedelta
from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)

ALLOWED_LB_FLAVORS = ('lb-small',
                      )
ALLOWED_POOL_ALGORITHMUS = ('round_robin',
                            'least_connections',
                            'source_ip',
                            )
ALLOWED_POOL_PROTOCOLS = ('tcp',
                          'proxy',
                          'proxyv2',
                          )
ALLOWED_HEALTH_MONITOR_TYPES = ('ping',
                                'tcp',
                                'http',
                                'https',
                                'tls-hello',
                                )
ALLOWED_HEALTH_MONITOR_HTTP = ('http',
                               'https',
                               )


class AnsibleCloudscaleLoadBalancer(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleLoadBalancer, self).__init__(module)

        # Initialize load balancer dictionary
        self._info = {}

    def _init_load_balancer_container(self):
        return {
            'uuid': self._module.params.get('uuid') or self._info.get('uuid'),
            'name': self._module.params.get('name') or self._info.get('name'),
            'state': 'absent',
        }

    def _get_load_balancer(self, refresh=False):
        if self._info and not refresh:
            return self._info

        self._info = self._init_load_balancer_container()

        uuid = self._info.get('uuid')
        if uuid is not None:
            load_balancer_info = self._get('load-balancers/%s' % uuid)
            if load_balancer_info:
                self._info = self._transform_state(load_balancer_info)

        else:
            name = self._info.get('name')
            if name is not None:
                load_balancers = self._get('load_balancers') or []
                matching_load_balancer = []
                for load_balancer in load_balancers:
                    if load_balancer['name'] == name:
                        matching_load_balancer.append(load_balancer)

                if len(matching_load_balancer) == 1:
                    self._info = self._transform_state(matching_load_balancer[0])
                elif len(matching_load_balancer) > 1:
                    self._module.fail_json(msg="More than one server with name '%s' exists. "
                                           "Use the 'uuid' parameter to identify the server." % name)

        return self._info

    def _create_load_balancer(self, load_balancer_info):
        self._result['changed'] = True

        data = deepcopy(self._module.params)
        for i in ('name', 'zone', 'flavor', 'vip_addresses', 'tags', 'api_timeout', 'api_token', 'api_url'):
            del data[i]

        self._result['diff']['before'] = self._init_load_balancer_container()
        self._result['diff']['after'] = deepcopy(data)
        if not self._module.check_mode:
            self._post('load_balancers', data)
            load_balancer_info = self._wait_for_state(('running', ))
        return load_balancer_info


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(),
        zone=dict(),
        flavor=dict(choices=ALLOWED_LB_FLAVORS),
        vip_addresses=dict(
            type='dict',
            options=dict(
                subnet=dict(type='str'),
                address=dict(type='str'),
            ),
        ),
        tags=dict(type='dict'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(),
        required_one_of=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    cloudscale_load_balancer = AnsibleCloudscaleLoadBalancer(module)
    if module.params['state'] == "absent":
        load_balancer = cloudscale_load_balancer.absent()
    else:
        load_balancer = cloudscale_load_balancer.present()

    result = cloudscale_load_balancer.get_result(load_balancer)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
