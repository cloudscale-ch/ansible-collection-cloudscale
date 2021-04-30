#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Ciril Troxler <ciril.troxler@cloudscale.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: custom_image
short_description: Manage custom images on the cloudscale.ch IaaS service
description:
  - Import, modify and delete custom images.
notes:
  - To import a new custom-image the I(url) and I(name) options are required.
author:
  - Ciril Troxler (@ctx)
version_added: 2.2.0
options:
  url:
    description:
      - The URL used to download the image.
    type: str
  name:
    description:
      - The human readable name of the custom image. Either name or UUID must
        be present to change an existing image.
    type: str
  uuid:
    description:
      - The unique identifier of the custom image import. Either name or UUID
        must be present to change an existing image
    type: str
  slug:
    description:
      - A string identifying the custom image for use within the API.
    type: str
  user_data_handling:
    description:
      - How user_data will be handled when creating a server. There are
        currently two options, "pass-through" and "extend-cloud-config".
    type: str
    choices: [ pass-through, extend-cloud-config ]
  zones:
    description:
      - Specify zones in which the custom image will be available (e.g. C(lpg1)
        or C(rma1)).
    type: list
    elements: str
  source_format:
    description:
      - The file format of the image referenced in the url. Currently only raw
        is supported.
    type: str
  tags:
    description:
      - The tags assigned to the custom image.
    type: dict
  state:
    description: State of the coustom image.
    choices: [ present, absent ]
    default: present
    type: str
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = r'''
- name: Import custom image
  cloudscale_ch.cloud.custom_image:
    name: "My Custom Image"
    url: https://ubuntu.com/downloads/hirsute.img
    slug: my-custom-image
    user_data_handling: extend-cloud-config
    zones: lpg1
    tags:
      project: luna
    state: present
  register: my_custom_image

- name: Wait until import succeeded
  cloudscale_ch.cloud.custom_image:
    uuid: "{{ my_custom_image.uuid }}"
  retries: 15
  delay: 5
  register: image
  until: image.import_status == 'success'
  failed_when: image.import_status == 'failed'

- name: Import custom image and wait until import succeeded
  cloudscale_ch.cloud.custom_image:
    name: "My Custom Image"
    url: https://ubuntu.com/downloads/hirsute.img
    slug: my-custom-image
    user_data_handling: extend-cloud-config
    zones: lpg1
    tags:
      project: luna
    state: present
  retries: 15
  delay: 5
  register: image
  until: image.import_status == 'success'
  failed_when: image.import_status == 'failed'

- name: Update custom image
  cloudscale_ch.cloud.custom_image:
    name: "My Custom Image"
    slug: my-custom-image
    user_data_handling: extend-cloud-config
    tags:
      project: luna
    state: present

- name: Delete custom image
  cloudscale_ch.cloud.custom_image:
    uuid: '{{ my_custom_image.uuid }}'
    state: absent

- name: List all custom images
  uri:
    url: 'https://api.cloudscale.ch/v1/custom-images'
    headers:
      Authorization: 'Bearer {{ query("env", "CLOUDSCALE_API_TOKEN") }}'
    status_code: 200
  register: image_list
  until: image_list is not failed
  retries: 5
  delay: 3
- name: Search the image list for all images with name 'My Custom Image'
  assert:
    that:
      - image_list.json | selectattr("name","search", "My Custom Image" )
'''

RETURN = r'''
href:
  description: The API URL to get details about this resource.
  returned: success when state == present
  type: str
  sample: https://api.cloudscale.ch/v1/custom-imges/11111111-1864-4608-853a-0771b6885a3a
uuid:
  description: The unique identifier of the custom image.
  returned: success
  type: str
  sample: 11111111-1864-4608-853a-0771b6885a3a
name:
  description: The human readable name of the custom image.
  returned: success
  type: str
  sample: alan
created_at:
  description: The creation date and time of the resource.
  returned: success
  type: str
  sample: "2020-05-29T13:18:42.511407Z"
slug:
  description: A string identifying the custom image for use within the API.
  returned: success
  type: str
  sample: foo
checksums:
  description: The checksums of the custom image as key and value pairs. The
    algorithm (e.g. sha256) name is in the key and the checksum in the value.
    The set of algorithms used might change in the future.
  returned: success
  type: dict
  sample: {
    "md5": "5b3a1f21cde154cfb522b582f44f1a87",
    "sha256": "5b03bcbd00b687e08791694e47d235a487c294e58ca3b1af704120123aa3f4e6"
  }
user_data_handling:
  description: How user_data will be handled when creating a server. There are
    currently two options, "pass-through" and "extend-cloud-config".
  returned: success
  type: str
  sample: "pass-through"
tags:
  description: Tags assosiated with the custom image.
  returned: success
  type: dict
  sample: { 'project': 'my project' }
import_status:
  description: Shows the progress of an import. Values are one of
    "in_progress", "success" or "error".
  returned: success
  type: str
  sample: "in_progress"
state:
  description: The current status of the custom image.
  returned: success
  type: str
  sample: present
'''

from copy import deepcopy

from ansible.module_utils.basic import (
    AnsibleModule,
)
from ansible.module_utils.urls import (
    fetch_url
)
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)
from ansible.module_utils._text import (
    to_text
)


class AnsibleCloudscaleCustomImage(AnsibleCloudscaleBase):

    def check_for_params(self, resource, keys, response=None, subkey=None):
        if isinstance(resource, dict):
            resource = [resource]

        result = []
        if response:
            if isinstance(response, dict):
                response = [response]
            for rc in resource:
                for rp in response:
                    if rc['uuid'] == rp['uuid']:
                        result.append(rc)
        else:
            for r in resource:
                for key in keys:
                    if key in self._module.params and self._module.params[key]:
                        if subkey and subkey in r:
                            if key in r[subkey] and r[subkey][key] == self._module.params[key]:
                                result.append(r)
                        else:
                            if key in r and r[key] == self._module.params[key]:
                                result.append(r)
                        break

        if len(result) == 1:
            result = result[0]
        return result

    def check_for_uuid(self, resources):
        if 'uuid' in self._module.params and self._module.params['uuid']:
            res = None
            for r in resources:
                if r['uuid'] == self._module.params['uuid']:
                    res = r
            return res
        else:
            return resources

    def fetch_both_urls(self, api_call, method='GET', data=None):
        if method == 'GET':
            headers = self._auth_header
        else:
            headers = self._auth_header.copy()
            headers['Content-type'] = 'application/json'

        # Get image information
        if self._api_url not in api_call:
            url = self._api_url + api_call
        else:
            url = api_call
        response, info = fetch_url(self._module,
                                   url,
                                   headers=headers,
                                   method=method,
                                   data=data,
                                   timeout=self._module.params['api_timeout'])

        # Add import to the url
        if api_call == 'custom-images':
            api_call = 'custom-images/import'
        else:
            # api_call is in the form custom-images/uuid and we need to add import in the middle
            api_call = api_call.replace('/', '/import/')

        if self._api_url not in api_call:
            url = self._api_url + api_call
        else:
            url = api_call

        # Get image import information
        response_import = []
        if method != 'PATCH':
            response_import, info_import = fetch_url(self._module,
                                                     url,
                                                     method=method,
                                                     headers=headers,
                                                     data=data,
                                                     timeout=self._module.params['api_timeout'])

            if info_import['status'] in (200, 201):
                response_import = self._module.from_json(to_text(response_import.read(),
                                                                 errors='surrogate_or_strict'))
        if info['status'] in (200, 201):
            response = self._module.from_json(to_text(response.read(), errors='surrogate_or_strict'))

        if response:
            response = self.check_for_params(response, ['uuid', 'name', 'slug', 'tags'])

        if response_import:
            if response:
                response_import = self.check_for_params(response_import,
                                                        ['uuid', 'name'],
                                                        response=response)
            else:
                response_import = self.check_for_params(response_import, ['name', 'uuid'], subkey='custom_image')

        if (not response) and response_import:
            # A new image is imported or a failed import with no image exists
            ensure_keys = {
                'created_at': None,
                'size_gb': 0,
                'checksums': 0,
                'user_data_handling': self._module.params['user_data_handling'],
                'zones': self._module.params['zones'],
                'slug': self._module.params['slug'],
                'import_status': 'Starting',
                'state': 'present'
            }

            if isinstance(response_import, dict):
                response = response_import['custom_image']
            else:
                response = response_import[0]['custom_image']
                response_import = response_import[0]

            if (self._module.params['url']
                    and response_import['url'] != self._module.params['url']
                    and response_import['status'] == 'failed'):
                # Don't return a failed import with the same name but a different url
                return [], info

            for key in ['error_message', 'tags', 'url']:
                response[key] = response_import[key]
            for key in ensure_keys:
                response[key] = ensure_keys[key]

            if 'status' in response_import:
                response['import_status'] = response_import['status']

            if method != 'POST':
                response = [response]
                response = self.check_for_uuid(response)

            return response, info_import

        copy_keys = {
            'status': 'import_status',
            'error_message': 'error_message',
            'url': 'url'
        }
        if info['status'] not in (200, 201):
            return [], info

        if isinstance(response_import, dict):
            response_import = [response_import]
        if isinstance(response, dict):
            # One image is found
            if isinstance(response_import, dict):
                response_import = [response_import]
            for r in response_import:
                if response['uuid'] == r['uuid']:
                    for key in copy_keys:
                        response[copy_keys[key]] = r[key]
            response = [response]
        else:
            # More than one image is found
            for r in response:
                for i in response_import:
                    if r['uuid'] == i['uuid']:
                        for key in copy_keys:
                            r[copy_keys[key]] = i[key]

        response = self.check_for_uuid(response)
        return response, info

    def _get(self, api_call):
        resp, info = self.fetch_both_urls(api_call)
        if info['status'] == 200:
            return resp
        elif info['status'] == 404:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with GET for '
                                   '"%s"' % api_call, fetch_url_info=info)

    def _post_or_patch(self, api_call, method, data, filter_none=True):
        # This helps with tags when we have the full API resource href to update.

        if data is not None:
            # Sanitize data dictionary
            # Deepcopy: Duplicate the data object for iteration, because
            # iterating an object and changing it at the same time is insecure
            for k, v in deepcopy(data).items():
                if filter_none and v is None:
                    del data[k]

            data = self._module.jsonify(data)

        resp, info = self.fetch_both_urls(api_call,
                                          method=method,
                                          data=data)

        if info['status'] in (200, 201):
            return resp
        elif info['status'] == 204:
            return None
        else:
            self._module.fail_json(msg='Failure while calling the cloudscale.ch API with %s for '
                                       '"%s".' % (method, api_call), fetch_url_info=info)

    def create(self, resource, data=None):
        if not self._module.params['url']:
            self._module.fail_json(msg="Cannot import a new image without url.")
        else:
            return super(AnsibleCloudscaleCustomImage, self).create(resource, data)


def main():
    argument_spec = cloudscale_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str'),
        slug=dict(type='str'),
        url=dict(type='str'),
        user_data_handling=dict(type='str',
                                choices=('pass-through',
                                         'extend-cloud-config')),
        uuid=dict(type='str'),
        tags=dict(type='dict'),
        state=dict(type='str', default='present',
                   choices=('present', 'absent')),
        zones=dict(type='list', elements='str'),
        source_format=dict(type='str'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid'),),
        supports_check_mode=True,
    )

    cloudscale_custom_image = AnsibleCloudscaleCustomImage(
        module,
        resource_name='custom-images',
        resource_key_uuid='uuid',
        resource_key_name='name',
        resource_create_param_keys=[
            'name',
            'slug',
            'url',
            'user_data_handling',
            'tags',
            'zones',
            'source_format',
        ],
        resource_update_param_keys=[
            'name',
            'slug',
            'user_data_handling',
            'tags',
        ],
    )

    if module.params['state'] == "absent":
        result = cloudscale_custom_image.absent()
    else:
        result = cloudscale_custom_image.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
