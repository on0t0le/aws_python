import logging
import boto3
from botocore.exceptions import ClientError
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']

ec2 = boto3.client(
    'ec2',
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name="eu-central-1"
)

response = ec2.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

try:
    response = ec2.create_security_group(GroupName='TestPySG',
                                         Description='Test description',
                                         VpcId=vpc_id)
    security_group_id = response['GroupId']
    print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

    data = ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '188.190.242.48/32'}]}
        ])
    print('Ingress Successfully Set %s' % data)
except ClientError as e:
    print(e)
