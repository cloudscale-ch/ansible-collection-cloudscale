# -*- coding: utf-8 -*-
# Copyright: (c) 2026, cloudscale.ch AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible_collections.cloudscale_ch.cloud.plugins.modules.interface import (
    AnsibleCloudscaleInterface,
)


@pytest.fixture
def interface(make_module):
    module = make_module(params={
        'router': 'router-uuid',
        'network': 'network-uuid',
    })
    return AnsibleCloudscaleInterface(module)


def _live(address, subnet_uuid):
    # Mimic what the API returns: address objects carry extra fields and the
    # subnet is a stub dict rather than a bare uuid.
    return {
        'address': address,
        'version': 4,
        'reverse_ptr': 'ptr.example.com',
        'subnet': {
            'uuid': subnet_uuid,
            'href': 'https://api/subnets/%s' % subnet_uuid,
        },
    }


class TestAddressesDifference:

    def test_equal_ignoring_order_and_extra_fields(self, interface):
        resource = {'addresses': [_live('172.16.0.2', 's2'),
                                  _live('172.16.0.1', 's1')]}
        param = [
            {'address': '172.16.0.1', 'subnet': 's1'},
            {'address': '172.16.0.2', 'subnet': 's2'},
        ]

        assert interface.find_difference('addresses', resource, param) is False

    def test_changed_address(self, interface):
        resource = {'addresses': [_live('172.16.0.1', 's1')]}
        param = [{'address': '172.16.0.9', 'subnet': 's1'}]

        assert interface.find_difference('addresses', resource, param) is True

    def test_changed_subnet(self, interface):
        resource = {'addresses': [_live('172.16.0.1', 's1')]}
        param = [{'address': '172.16.0.1', 'subnet': 's2'}]

        assert interface.find_difference('addresses', resource, param) is True

    def test_empty_on_both_sides(self, interface):
        assert interface.find_difference('addresses', {'addresses': []}, []) is False


class TestOtherKeysDelegateToBase:

    def test_non_address_key_uses_super(self, interface):
        assert interface.find_difference('name', {'name': 'old'}, 'new') is True
        assert interface.find_difference('name', {'name': 'x'}, 'x') is False
