# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, Gaudenz Steinlin <gaudenz.steinlin@cloudscale.ch>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text

API_URL = 'https://api.cloudscale.ch/v1/'


def cloudscale_argument_spec():
    return dict(
        api_token=dict(fallback=(env_fallback, ['CLOUDSCALE_API_TOKEN']),
                       no_log=True,
                       required=True),
        api_timeout=dict(default=30, type='int'),
    )


class AnsibleCloudscaleApi(object):

    def __init__(self, module):
        self._module = module
        self._auth_header = {'Authorization': 'Bearer %s' % module.params['api_token']}

    def _get(self, api_call):
        resp, info = fetch_url(self._module, API_URL + api_call,
                               headers=self._auth_header,
                               timeout=self._module.params['api_timeout'])

        if info['status'] == 200:
            return self._module.from_json(to_text(resp.read(), errors='surrogate_or_strict'))
        elif info['status'] == 404:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with GET for '
                                       '"%s".' % api_call, fetch_url_info=info)

    def _post_or_patch(self, api_call, method, data):
        # This helps with tags when we have the full API resource href to update.
        if API_URL not in api_call:
            api_endpoint = API_URL + api_call
        else:
            api_endpoint = api_call

        headers = self._auth_header.copy()
        if data is not None:
            # Sanitize data dictionary
            # Deepcopy: Duplicate the data object for iteration, because
            # iterating an object and changing it at the same time is insecure
            for k, v in deepcopy(data).items():
                if v is None:
                    del data[k]

            data = self._module.jsonify(data)
            headers['Content-type'] = 'application/json'

        resp, info = fetch_url(self._module,
                               api_endpoint,
                               headers=headers,
                               method=method,
                               data=data,
                               timeout=self._module.params['api_timeout'])

        if info['status'] in (200, 201):
            return self._module.from_json(to_text(resp.read(), errors='surrogate_or_strict'))
        elif info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with %s for '
                                       '"%s".' % (method, api_call), fetch_url_info=info)

    def _post(self, api_call, data=None):
        return self._post_or_patch(api_call, 'POST', data)

    def _patch(self, api_call, data=None):
        return self._post_or_patch(api_call, 'PATCH', data)

    def _delete(self, api_call):
        resp, info = fetch_url(self._module,
                               API_URL + api_call,
                               headers=self._auth_header,
                               method='DELETE',
                               timeout=self._module.params['api_timeout'])

        if info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with DELETE for '
                                       '"%s".' % api_call, fetch_url_info=info)


class AnsibleCloudscaleCommon(AnsibleCloudscaleApi):

    def __init__(
        self,
        module,
        resource_name='',
        resource_key_uuid='uuid',
        resource_key_name='name',
        resource_create_param_keys=None,
        resource_update_param_keys=None,
    ):
        super(AnsibleCloudscaleCommon, self).__init__(module)
        self._result = {
            'changed': False,
            'diff': dict(
                before=dict(),
                after=dict()
            ),
        }
        self._resource_data = dict()

        # The identifier key of the resource, usually 'uuid'
        self.resource_key_uuid = resource_key_uuid

        # The name key of the resource, usually 'name'
        self.resource_key_name = resource_key_name

        # The API resource e.g server-group
        self.resource_name = resource_name

        # List of params used to create the resource
        self.resource_create_param_keys = resource_create_param_keys or ['name']

        # List of params used to update the resource
        self.resource_update_param_keys = resource_update_param_keys or ['name']

    def _init_resource(self):
        return {
            'state': "absent",
            self.resource_key_uuid: self._module.params.get(self.resource_key_uuid) or self._resource_data.get(self.resource_key_uuid),
            self.resource_key_name: self._module.params.get(self.resource_key_name) or self._resource_data.get(self.resource_key_name),
        }

    def query(self):
        # Query by UUID
        uuid = self._module.params[self.resource_key_uuid]
        if uuid is not None:
            resource = self._get('%s/%s' % (self.resource_name, uuid))
            if resource:
                self._resource_data = resource

        # Query by name
        else:
            name = self._module.params[self.resource_key_name]
            matching = []
            resources = self._get('%s' % self.resource_name)
            for resource in resources:
                if resource[self.resource_key_name] == name:
                    matching.append(resource)

            # Fail on more than one resource with identical name
            if len(matching) > 1:
                self._module.fail_json(
                    msg="More than one %s resource with '%s' exists: %s. "
                        "Use the '%s' parameter to identify the resource." % (
                            self.resource_name,
                            self.resource_key_name,
                            name,
                            self.resource_key_uuid
                        )
                )
            elif len(matching) == 1:
                self._resource_data = matching[0]
        return self._resource_data

    def create(self):
        # Fail if UUID/ID was provided but the resource was not found on state=present.
        uuid = self._module.params.get(self.resource_key_uuid)
        if uuid is not None:
            self._module.fail_json(msg="The resource with UUID '%s' was not found "
                                   "and we would create a new one with different UUID, "
                                   "this is probably not want you have asked for." % uuid)

        self._result['changed'] = True
        resource = dict()

        data = dict()
        for param in self.resource_create_param_keys:
            data[param] = self._module.params.get(param)

        self._result['diff']['before'] = self._init_resource()
        self._result['diff']['after'] = deepcopy(data)

        if not self._module.check_mode:
            resource = self._post(self.resource_name, data)
        return resource

    def update(self, resouce):
        updated = False
        for param in self.resource_update_param_keys:
            updated = self._param_updated(param, resouce) or updated

        # Refresh if resource was updated in live mode
        if updated and not self._module.check_mode:
            resouce = self.query()
        return resouce

    def present(self):
        resource = self.query()
        if not resource:
            resource = self.create()
        else:
            resource = self.update(resource)
        return self.get_result(resource)

    def absent(self):
        resource = self.query()
        if resource:
            self._result['changed'] = True
            self._result['diff']['before'] = deepcopy(resource)
            self._result['diff']['after'] = self._init_resource()

            if not self._module.check_mode:
                self._delete('%s/%s' % (self.resource_name, resource[self.resource_key_uuid]))
        return self.get_result(resource)

    def _param_updated(self, key, resource):
        param = self._module.params.get(key)
        if param is None:
            return False

        if resource and key in resource:
            if param != resource[key]:
                self._result['changed'] = True

                patch_data = {
                    key: param
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

    def get_result(self, resource):
        if resource:
            resource['state'] = "present"
        else:
            resource = self._init_resource()

        for k, v in resource.items():
            self._result[k] = v
        return self._result


class AnsibleCloudscaleBase(AnsibleCloudscaleCommon):

    def __init__(self, module):
        super(AnsibleCloudscaleBase, self).__init__(module)

    def get_result(self, resource):
        if resource:
            for k, v in resource.items():
                self._result[k] = v
        return self._result
