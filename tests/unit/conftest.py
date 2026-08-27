# -*- coding: utf-8 -*-
# Copyright: (c) 2026, cloudscale.ch AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock

import pytest

from ansible_collections.cloudscale_ch.cloud.tests.unit.utils import FailJson


@pytest.fixture
def make_module():
    """Return a factory building a fake AnsibleModule.
    """
    def _make(params=None, check_mode=False):
        module = MagicMock()
        base = {
            'api_url': 'https://api.cloudscale.ch/v1',
            'api_token': 'token',
            'api_timeout': 45,
        }
        base.update(params or {})
        module.params = base
        module.check_mode = check_mode

        def _fail_json(**kwargs):
            raise FailJson(**kwargs)

        module.fail_json.side_effect = _fail_json
        return module

    return _make
