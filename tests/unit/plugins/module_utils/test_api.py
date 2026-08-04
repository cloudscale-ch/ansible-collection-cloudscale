# -*- coding: utf-8 -*-
# Copyright: (c) 2026, cloudscale.ch AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock

import pytest

from ansible_collections.cloudscale_ch.cloud.tests.unit.utils import FailJson
from ansible_collections.cloudscale_ch.cloud.plugins.module_utils.api import (
    AnsibleCloudscaleBase,
)


class TestCreateUUIDCheck:

    def test_uuid_without_recreate_fails(self, make_module):
        module = make_module(params={'uuid': 'abc', 'name': 'foo'})
        base = AnsibleCloudscaleBase(module)

        with pytest.raises(FailJson) as exc:
            base.create({})

        assert "'abc'" in exc.value.kwargs['msg']

    def test_create_check_mode_skips_post(self, make_module):
        module = make_module(params={'name': 'foo'}, check_mode=True)
        base = AnsibleCloudscaleBase(module, resource_create_param_keys=['name'])
        base._post = MagicMock()

        base.create({})

        base._post.assert_not_called()
        assert base._result['changed'] is True


class TestHasDifferences:
    @pytest.mark.parametrize(
        'create_keys,resource,params,expected',
        [
            # No difference - params match resource
            (['name'], {'name': 'test'}, {'name': 'test'}, False),
            # Has difference - params don't match
            (['name'], {'name': 'old'}, {'name': 'new'}, True),
            # No difference - param is None
            (['name'], {'name': 'test'}, {'name': None}, False),
            # No difference - resource empty
            (['name'], {}, {'name': 'test'}, False),
            # No difference - key not in a non-empty resource
            (['name'], {'other': 'x'}, {'name': 'test'}, False),
            # Multiple keys - all match
            (['name', 'description'], {'name': 'test', 'description': 'desc'}, {'name': 'test', 'description': 'desc'}, False),
            # Multiple keys - first differs
            (['name', 'description'], {'name': 'old', 'description': 'desc'}, {'name': 'new', 'description': 'desc'}, True),
            # Multiple keys - second differs
            (['name', 'description'], {'name': 'test', 'description': 'old'}, {'name': 'test', 'description': 'new'}, True),
        ]
    )
    def test_has_differences_basic(self, make_module, create_keys, resource, params, expected):
        module = make_module(params=params)
        base = AnsibleCloudscaleBase(module, resource_create_param_keys=create_keys)
        assert base.has_differences(resource) == expected

    def test_has_differences_href_stub(self, make_module):
        """Test difference detection when resource contains href stubs."""
        module = make_module(params={'network': 'different-uuid'})
        base = AnsibleCloudscaleBase(module, resource_create_param_keys=['network'])

        resource = {'network': {'href': 'https://api.cloudscale.ch/v1/networks/uuid-123'}}
        assert base.has_differences(resource) is True

        # Matching UUID (reuses resources above)
        module = make_module(params={'network': 'uuid-123'})
        base = AnsibleCloudscaleBase(module, resource_create_param_keys=['network'])
        assert base.has_differences(resource) is False
