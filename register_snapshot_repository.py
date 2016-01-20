#!/usr/bin/python
# encoding: utf-8

# (c) 2015, Jose Armesto <jose@armesto.net>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = """
---
module: register_snapshot_repository
short_description: Registers a Snapshot Directory for ElasticSearch Snapshots
description:
  - It depends on boto

version_added: "2.1"
author: "Jose Armesto (@fiunchinho)"
options:
  region:
    description:
      - The AWS region to use.
    required: true
    aliases: ['aws_region', 'ec2_region']
  elasticsearch_host:
    description:
      - ElasticSearch endpoint
    required: true
  role_arn:
    description:
      - ARN of the role to use for the S3 bucket
    required: true
  bucket:
    description:
      - S3 bucket where repository will be saved
    required: true
  snapshot_repository_name:
    description:
      - Name of the repository where snapshots will be saved
    default: null
    required: true
  profile:
    description:
      - Boto profile to use.
    required: true
requirements:
  - "python >= 2.6"
  - boto
"""

EXAMPLES = '''

- register_snapshot_repository:
    profile: "pro"
    region: "eu-west-1"
    elasticsearch_host: "logs-q213lkjalsjda.eu-west-1.es.amazonaws.com"
    role_arn: "arn:aws:iam::1234456778:role/S3ElasticSearchLogs"
    bucket: "logs"
    snapshot_repository_name: "s3snapshots"
'''
try:
    import boto.ec2
    HAS_BOTO=True
except ImportError:
    HAS_BOTO=False

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            region = dict(required=True, aliases = ['aws_region', 'ec2_region']),
            es_host = dict(required=True, aliases = ['elasticsearch_host']),
            profile = dict(required=True),
            role_arn = dict(required=True),
            bucket = dict(required=True),
            repository_name = dict(required=True, aliases = ['snapshot_repository_name']),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module, install via pip or your package manager')

    try:
        aws_auth_connection = ESConnection(profile_name=module.params.get('profile'), region=module.params.get('region'), host=module.params.get('es_host'), is_secure=False)
    except (boto.exception.NoAuthHandlerFound, StandardError), e:
        module.fail_json(msg=str(e))

    resp = aws_auth_connection.make_request(
            method='POST',
            path='/_snapshot/' + module.params.get('repository_name'),
            data='{"type": "s3", "settings": { "bucket": "' + module.params.get('bucket') + '", "region": "' + module.params.get('region') + '", "role_arn": "' + module.params.get('role_arn') + '"}}')

    module.exit_json(changed=True, resp=resp.read())


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *
from boto.connection import AWSAuthConnection

class ESConnection(AWSAuthConnection):

    def __init__(self, region, **kwargs):
        super(ESConnection, self).__init__(**kwargs)
        self._set_auth_region_name(region)
        self._set_auth_service_name("es")

    def _required_auth_capability(self):
        return ['hmac-v4']

if __name__ == '__main__':
    main()