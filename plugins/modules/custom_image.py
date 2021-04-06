#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021, Ciril Troxler<ciril.troxler@cloudscale.ch>
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
    choices: [ pass-through , extend-cloud-config ]
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
    default: "raw"
    choices: [ raw ]
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
  import_status:
    description: Get the import status of a new custom image.
    type: bool
    choices: [ true, false ]
    default: false
  force:
    description: Import an image
    choices: [ true, false ]
    default: false
    type: bool
extends_documentation_fragment: cloudscale_ch.cloud.api_parameters
'''

EXAMPLES = r'''
- name: Import custom image
  cloudscale_ch.cloud.custom_image:
    name: "My Custom Image"
    url: https://ubuntu.com/downloads/hirsute.img
    slug: my-custom-image
    user_data_handling: extended-cloud-config
    zones: LPG1
    tags:
      project: luna
    state: present

- name: Wait until import succeeded
  cloudscale_ch.cloud.custom_image:
    uuid: 11111111-1864-4608-853a-0771b6885a3a
    import_status: true
  retries: 15
  delay: 5
  register: import_status
  until: import_status.status == 'success'

- name: Update custom image
  cloudscale_ch.cloud.custom_image:
    name: "My Custom Image"
    slug: SLUG
    user_data_handling: extended-cloud-config
    tags:
      project: luna
    state: present

- name: Delete custom image
  cloudscale_ch.cloud.custom_image:
    uuid: '{{ my_custom_image.uuid }}'
    state: absent
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
status:
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

from ansible.module_utils.basic import (
    AnsibleModule,
)
from ..module_utils.api import (
    AnsibleCloudscaleBase,
    cloudscale_argument_spec,
)


class AnsibleCloudscaleCustomImages(AnsibleCloudscaleBase):

    def query(self):

        # Initialize
        self._resource_data = self.init_resource()

        # Set import status
        import_status = self._module.params.pop('import_status', False)

        # Query by UUID
        uuid = self._module.params[self.resource_key_uuid]

        if uuid is not None:

            # Get image by uuid
            resource = self._get('%s/%s' % (self.resource_name, uuid))

            updated = False
            if resource:
                # Check if slug, tags or user_data_handling needs update
                for key in ['slug', 'tags', 'user_data_handling']:
                    if self._module.params[key] is not None:
                        if self.find_difference(key,
                                                resource,
                                                self._module.params[key]):
                            updated = True

            # Get image import status by uuid
            if not updated and not self._module.params['state'] == 'absent':
                if import_status is True:
                    self.resource_name += '/import'
                resource = self._get('%s/%s' % (self.resource_name, uuid))
            if resource:
                self._resource_data = resource
                self._resource_data['state'] = 'present'
        else:
            # Get all images
            resources = self._get('%s' % (self.resource_name))
            # Remove images with other names from result
            if self._module.params['name'] is not None:
                key = 'name'
            elif self._module.params['slug'] is not None:
                key = 'slug'
            elif self._module.params['tags'] is not None:
                key = 'tags'
            else:
                raise NotImplementedError("Unknown key: %s" % key)

            resources = [r for r in resources
                         if r[key] == self._module.params[key]]

            # Return newest image if at least one is found
            # and force is not true
            if len(resources) >= 1 and not self._module.params['force']:
                self._resource_data = sorted(resources,
                                             key=lambda
                                             item: item['created_at'],
                                             reverse=True)[0]
                self._resource_data['state'] = 'present'
            # Import new image
            elif self._module.params['url'] is not None:
                del self._module.params['force']
                self._resource_data['state'] = 'absent'
                self.resource_name += '/import'
        return self.pre_transform(self._resource_data)


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
        source_format=dict(type='str', default='raw', choices=('raw', )),
        import_status=dict(type='bool', choices=(True, False), default=False),
        force=dict(type='bool', default=False, choices=(True, False))
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(('name', 'uuid', 'slug', 'tags'),),
        required_if=(('state', 'absent', ('uuid',)),),
        supports_check_mode=True,
    )

    cloudscale_custom_image = AnsibleCloudscaleCustomImages(
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
            'import_status',
            'force',
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
        cloudscale_custom_image.resource_name = 'custom-images'
        result = cloudscale_custom_image.present()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
