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

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *
from boto.connection import AWSAuthConnection

DOCUMENTATION = """
---
module: aws_elasticsearch_snapshot
short_description: Registers a Snapshot Directory, or take snapshots for ElasticSearch Snapshots.
description:
  - It depends on boto
  - If bucket and role_arn are specified, snapshot repository will be created.
  - If snapshot name is specified, snapshot will be taken.

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
    default: null
  bucket:
    description:
      - S3 bucket where repository will be saved
    default: null
  snapshot_repository_name:
    description:
      - Name of the repository where snapshots will be saved
    default: null
    required: true
  snapshot_name:
    description:
      - When taken snapshot, the name for the snapshot
    default: null
  aws_access_key:
    description:
      - AWS access key to sign the requests.
    required: true
    aliases: ['aws_access_key', 'ec2_access_key']
  aws_secret_key:
    description:
      - AWS secret key to sign the requests.
    required: true
    aliases: ['aws_secret_key', 'ec2_secret_key']
  profile:
    description:
      - Profile from .aws/credentials file to use for authenticating with AWS
    required false
requirements:
  - "python >= 2.6"
  - boto
"""

EXAMPLES = '''

- aws_elasticsearch_snapshot:
    region: "eu-west-1"
    aws_access_key: "AKIAJ5CC6CARRKOX5V7Q"
    aws_secret_key: "cfDKFSXEo1CC6gfhfhCARRKOX5V7Q"
    elasticsearch_host: "logs-q213lkjalsjda.eu-west-1.es.amazonaws.com"
    role_arn: "arn:aws:iam::1234456778:role/S3ElasticSearchLogs"
    bucket: "logs"
    snapshot_repository_name: "s3snapshots"

- aws_elasticsearch_snapshot:
    region: "eu-west-1"
    profile: "production"
    elasticsearch_host: "logs-q213lkjalsjda.eu-west-1.es.amazonaws.com"
    snapshot_repository_name: "s3snapshots"
    snapshot_name: "2016-02-01"
'''
try:
    import boto.ec2

    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    boto = None


def get_elasticsearch_connection(aws_access_key, aws_secret_key, region, host, profile_name):
    return ESConnection(aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key,
                        region=region, host=host, is_secure=False, profile_name=profile_name)


def create_snapshot_repository(es_connection, repository_name, bucket, region, role_arn):
    return es_connection.make_request(
        method='POST',
        path='/_snapshot/' + repository_name,
        data='{"type": "s3", "settings": { "bucket": "' + bucket + '", "region": "' + region +
             '", "role_arn": "' + role_arn + '"}}')


def take_snapshot(es_connection, repository_name, snapshot_name):
    return es_connection.make_request(
        method='PUT',
        path='/_snapshot/' + repository_name + '/' + snapshot_name)


def do_main(module):
    repository_name = module.params.get('repository_name')
    snapshot_name = module.params.get('snapshot_name')
    bucket = module.params.get('bucket')
    region = module.params.get('region')
    role_arn = module.params.get('role_arn')
    aws_access_key = module.params.get('aws_access_key')
    aws_secret_key = module.params.get('aws_secret_key')
    host = module.params.get('host')
    profile_name = module.params.get('profile')

    es_connection = get_elasticsearch_connection(aws_access_key, aws_secret_key, region, host,
                                                 profile_name)

    if bucket and role_arn:
        return create_snapshot_repository(es_connection, repository_name, bucket, region, role_arn)
    elif snapshot_name:
        return take_snapshot(es_connection, repository_name, snapshot_name)
    else:
        raise ValueError('Required parameters are missing')


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        host=dict(required=True, aliases=['elasticsearch_host']),
        role_arn=dict(),
        bucket=dict(),
        snapshot_name=dict(),
        repository_name=dict(required=True, aliases=['snapshot_repository_name']),
    )
    )

    ansible_module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        ansible_module.fail_json(msg='boto required for this module, install via pip or '
                                     'your package manager')

    try:
        ansible_module.exit_json(changed=True, resp=do_main(ansible_module).read())
    except (boto.exception.NoAuthHandlerFound, StandardError), e:
        ansible_module.fail_json(msg=str(e))


class ESConnection(AWSAuthConnection):
    def __init__(self, region, **kwargs):
        super(ESConnection, self).__init__(**kwargs)
        self._set_auth_region_name(region)
        self._set_auth_service_name("es")

    def _required_auth_capability(self):
        return ['hmac-v4']


if __name__ == '__main__':
    main()
