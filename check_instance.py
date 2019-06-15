import boto3
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']
region = 'eu-central-1'
instance_name = 'TestEC2'

ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )

instances = ec2_client.describe_instances(
    Filters=[
        {
            'Name': 'tag:Name',
            'Values': [ instance_name ]
        }
    ])
if instances['Reservations']:
    for instance in instances['Reservations']:
        print(instance['Instances'][0]['PublicIpAddress'])
else:
    print(instances)