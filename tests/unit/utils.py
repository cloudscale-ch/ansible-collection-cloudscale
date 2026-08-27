# -*- coding: utf-8 -*-
# Copyright: (c) 2026, cloudscale.ch AG
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class FailJson(Exception):
    """Raised in place of AnsibleModule.fail_json so tests can assert on it.
    """

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        super(FailJson, self).__init__(kwargs.get('msg'))
