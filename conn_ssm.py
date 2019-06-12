import boto3
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']
region = 'eu-central-1'

def create_security_group(ec2,groupName,vpc_id):
    for sec_group in ec2.describe_security_groups()['SecurityGroups']:
        if sec_group['GroupName'] == groupName:
            print(sec_group['GroupId'])
            return (sec_group['GroupId'])

    # Security Group was not found, create it
    sec_group = ec2.create_security_group(
        GroupName=groupName, Description='This is a test', VpcId=vpc_id)
    sec_group_id = sec_group['GroupId']

    ec2.authorize_security_group_ingress(
        GroupId=sec_group_id,
        IpPermissions=[
                    {'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                    {'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '188.190.242.48/32'}]}
                ]
    )
    print(sec_group_id)
    return(sec_group_id)

ec2 = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )

vpc = ec2.describe_vpcs()
vpc_id = vpc.get('Vpcs', [{}])[0].get('VpcId', '')
print('VPC is %s' %(vpc_id))

subnet = ec2.describe_subnets(
    Filters=[
        {
            'Name': 'vpc-id',
            'Values': [
                vpc_id
            ]
        },
    ]
)
subnet_id = subnet.get('Subnets',[{}])[0].get('SubnetId', '')
print('Subnet id is %s' %(subnet_id))

# Create sec group
sg_id = create_security_group(ec2,'TestGroup',vpc_id)

def create_instance():

    image_id = 'ami-0ebe657bc328d4e82'
    instance_type = 't2.micro'
    keypair_name = 'aperture-web1'
    instance_name = 'TestEC2'

    params = {
                'ImageId': image_id,
                'InstanceType': instance_type,
                'MinCount': 1,
                'MaxCount': 1,
                'KeyName': keypair_name,
                'NetworkInterfaces' : [{'SubnetId': subnet_id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True, 'Groups': [sg_id]}],
                'TagSpecifications' : [{
                    'ResourceType':'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name
                        }
                    ]
                }]
            }
    
    instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:Name',
                'Values': [ instance_name ]
            }
        ])
    if instances['Reservations']:
        for instance in instances['Reservations']:
            print(instance['Instances'][0]['InstanceId'])
            return instance['Instances'][0]['InstanceId']

    # Instance was not found, create it

    instances = ec2.run_instances(**params)

    waiter = ec2.get_waiter('instance_running')

    instance_id = instances['Instances'][0]['InstanceId']
    waiter.wait(InstanceIds=[instance_id])    
    #print(instances['Instances'][0]["State"]["Name"])
    return instance_id

instance_id = create_instance()

ssm_client = boto3.client('ssm',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region)

# resp = ssm_client.describe_instance_information(
#     InstanceInformationFilterList=[
#         {
#             'key': 'InstanceIds',
#             'valueSet': [
#                 instance_id
#             ]
#         },
#     ]
# )

# print(resp)
response = ssm_client.send_command(
            Targets=[
                {
                    'Key': 'InstanceIds',
                    'Values': [
                        'i-02a5b2316539404cd',
                    ]
                },
            ],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": ["echo test"]
            })

command_id = response['Command']['CommandId']
output = ssm_client.get_command_invocation(
      CommandId=command_id,
      InstanceId=instance_id,
    )
print(output)