==============================================
Ansible Collection cloudscale.ch Release Notes
==============================================

.. contents:: Topics


v1.3.0
======

Minor Changes
-------------

- floating_ip - Added an optional name parameter to gain idempotency. The parameter will be required for assigning a new floating IP with release of version 2.0.0 (https://github.com/cloudscale-ch/ansible-collection-cloudscale/pull/43/).
- floating_ip - Allow to reserve an IP without assignment to a server (https://github.com/cloudscale-ch/ansible-collection-cloudscale/pull/31/).

New Modules
-----------

- subnet - Manages subnets on the cloudscale.ch IaaS service

v1.2.0
======

Minor Changes
-------------

- server_group - The module has been refactored and the code simplifed (https://github.com/cloudscale-ch/ansible-collection-cloudscale/pull/23).
- volume - The module has been refactored and the code simplifed (https://github.com/cloudscale-ch/ansible-collection-cloudscale/pull/24).

New Modules
-----------

- network - Manages networks on the cloudscale.ch IaaS service

v1.1.0
======

Minor Changes
-------------

- floating_ip - added tags support (https://github.com/cloudscale-ch/ansible-collection-cloudscale/pull/16)

New Modules
-----------

- objects_user - Manages objects users on the cloudscale.ch IaaS service
