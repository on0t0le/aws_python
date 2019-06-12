import boto3
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']
region = 'eu-central-1'

ec2 = boto3.resource('ec2', aws_access_key_id=access_key_id,
                     aws_secret_access_key=secret_access_key,
                     region_name=region)

response = ec2.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

# create subnet
subnet = ec2.create_subnet(CidrBlock='192.168.1.0/24', VpcId=vpc_id)
print(subnet.id)


# Create sec group
sec_group = ec2.create_security_group(
    GroupName='slice_0', Description='slice_0 sec group', VpcId=vpc_id)
sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='icmp',
    FromPort=-1,
    ToPort=-1
)
print(sec_group.id)

# Create instance
instances = ec2.create_instances(
    ImageId='ami-835b4efa', InstanceType='t2.micro', MaxCount=1, MinCount=1,
    NetworkInterfaces=[{'SubnetId': subnet.id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True, 'Groups': [sec_group.group_id]}])
instances[0].wait_until_running()
print(instances[0].id)