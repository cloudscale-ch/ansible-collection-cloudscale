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
  - Get, create, update, delete health monitors on the cloudscale.ch IaaS service.
notes:
  - If I(uuid) option is provided, it takes precedence over I(name) for load balancer health monitor selection. This allows to update the health monitor's name.
  - If no I(uuid) option is provided, I(name) is used for load balancer selection. If more than one load balancer with this name exists, execution is aborted.
author:
  - Gaudenz Steinlin (@gaudenz)
  - Kenneth Joss (@k-304)
version_added: "2.3.0"
options:
  state:
    description:
      - State of the load balancer.
    choices: [ present, absent ]
    default: present
    type: str
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





extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = '''

'''

RETURN = '''

'''

from ansible.module_utils.basic import AnsibleModule
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)

ALLOWED_STATES = ('present',
                  'absent',
                  )
ALLOWED_TYPES = ('ping',
                 'tcp',
                 'http',
                 'https',
                 'tls-hello',
                 )


class AnsibleCloudscaleLoadBalancerHealthMonitor(AnsibleCloudscaleBase):

    def __init__(self, module):
        super(AnsibleCloudscaleLoadBalancerHealthMonitor, self).__init__(
            module,
            resource_name='load-balancers/health-monitors',
            resource_key_name='pool',
            resource_create_param_keys=[
                'pool',
                'timeout_s',
                'up_threshold',
                'down_threshold',
                'type',
                'http',
                'tags',
            ],
            resource_update_param_keys=[
                'delay_s',
                'timeout_s',
                'up_threshold',
                'down_threshold',
                'expected_codes',
                'http',
                'tags',
            ],
        )

    def query(self):
        # Initialize
        self._resource_data = self.init_resource()

        resource_key_pool = 'pool'
        uuid = self._module.params[self.resource_key_uuid]
        pool = self._module.params[resource_key_pool]
        matching = []

        # Either search by given health monitor's UUID or
        # search the health monitor by its acossiated pool UUID (1:1)
        if uuid is not None:
            super().query()
        else:
            pool = self._module.params[resource_key_pool]
            if pool is not None:

                resources = self._get('%s' % (self.resource_name))

                if resources:
                    for health_monitor in resources:
                        if health_monitor[resource_key_pool]['uuid'] == pool:
                            matching.append(health_monitor)

            # Fail on more than one resource with identical name
            if len(matching) > 1:
                self._module.fail_json(
                    msg="More than one %s resource for pool '%s' exists." % (
                            self.resource_name,
                            resource_key_pool
                        )
                )
            elif len(matching) == 1:
                self._resource_data = matching[0]
                self._resource_data['state'] = "present"

        return self.pre_transform(self._resource_data)

    def update(self, resource):
        updated = False
        for param in self.resource_update_param_keys:
            if param == 'http':
                for param in ["expected_codes", "host", "method", "url_path"]:
                    updated = self._param_updated(param, resource) or updated
            else:
                updated = self._param_updated(param, resource) or updated

        # Refresh if resource was updated in live mode
        if updated and not self._module.check_mode:
            resource = self.query()
        return resource

    def _param_updated(self, key, resource):
        if key in ["expected_codes", "host", "method", "url_path"] and self._module.params.get('http') is not None:
            param = self._module.params.get('http')
            param = param[key]
            #if key == 'method' and param == "CONNECT":
            #    self._module.fail_json(msg=param)
        else:
            super()._param_updated(key, resource)

        if param is None:
            return False

        if not resource or key not in resource:
            return False

        is_different = self.find_difference(key, resource, param)

        if is_different:
            self._result['changed'] = True

            patch_data = {
                ['http'][key]: param
            }

            self._result['diff']['before'].update({key: resource[key]})
            self._result['diff']['after'].update(patch_data)

            if not self._module.check_mode:
                href = resource.get('href')
                if not href:
                    self._module.fail_json(msg='Unable to update %s, no href found.' % key)

                self._patch(href, patch_data)
                return True
        return False


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        uuid=dict(type='str', aliases=['name']),
        pool=dict(type='str'),
        delay_s=dict(type='int'),
        timeout_s=dict(type='int'),
        up_threshold=dict(type='int'),
        down_threshold=dict(type='int'),
        type=dict(type='str', choices=ALLOWED_TYPES),
        http=dict(
            type='dict',
            options=dict(
                expected_codes=dict(type='list'),
                method=dict(type='str'),
                url_path=dict(type='str'),
                version=dict(type='str'),
                host=dict(type='str'),
            )
        ),
        tags=dict(type='dict'),
        state=dict(default='present', choices=ALLOWED_STATES),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=(),
        required_one_of=(),
        required_if=(),
        supports_check_mode=True,
    )

    cloudscale_load_balancer_health_monitor = AnsibleCloudscaleLoadBalancerHealthMonitor(module)
    cloudscale_load_balancer_health_monitor.query_constraint_keys = []
    cloudscale_load_balancer_health_monitor.http_options = [
        'expected_codes',
        'method',
        'url_path',
        'host',
    ]

    if module.params['state'] == "absent":
        result = cloudscale_load_balancer_health_monitor.absent()
    else:
        result = cloudscale_load_balancer_health_monitor.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
