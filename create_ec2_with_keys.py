import boto3
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']
region = 'eu-central-1'
image_id = 'ami-0ebe657bc328d4e82'
instance_type = 't2.micro'
key_pair_name = 'testkeypy'
instance_name = 'TestEC2'

def create_ec2_instance(ec2_client,image_id,instance_type,instance_name,key_pair_name,sg_id):
    params = {
                'ImageId': image_id,
                'InstanceType': instance_type,
                'MinCount': 1,
                'MaxCount': 1,
                'KeyName': key_pair_name,
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
    
    instances = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name','Values': [ instance_name ]}])

    if instances['Reservations']:
        for reservations in instances['Reservations']:
            for instance in reservations['Instances']:
                if instance['State']['Name']=='running' or instance['State']['Name']=='pending':
                    print(instance['InstanceId'])
                    return instance['InstanceId']

    # Instance was not found, create it

    instances = ec2_client.run_instances(**params)

    instance_id = instances['Instances'][0]['InstanceId']

    #Wait instance running state
    run_waiter = ec2_client.get_waiter('instance_running')
    run_waiter.wait(InstanceIds=[instance_id])
    print('Instance %s is running, but NOT all checks' %(instance_id))

    #Wait instance OK state
    ok_waiter = ec2_client.get_waiter('instance_status_ok')
    ok_waiter.wait(InstanceIds=[instance_id])
    print('Instance %s is running succesfully!' %(instance_id))

    return instance_id

def create_pub_key():
    fp = open(os.path.expanduser('./test_key_public'))
    pub_key = fp.read()
    fp.close()
    return pub_key

def create_key_pair(ec2_client,key_pair_name):
    
    #Delete if exists
    if not ec2_client.describe_key_pairs(Filters=[{'Name': 'key-name','Values': [key_pair_name]}])['KeyPairs']:        
        pub_key = create_pub_key()
        ec2_client.import_key_pair(KeyName=key_pair_name,PublicKeyMaterial=pub_key)

def create_security_group(ec2_client,groupName,vpc_id):
    for sec_group in ec2_client.describe_security_groups()['SecurityGroups']:
        if sec_group['GroupName'] == groupName:
            print(sec_group['GroupId'])
            return (sec_group['GroupId'])

    # Security Group was not found, create it
    sec_group = ec2_client.create_security_group(
        GroupName=groupName, Description='This is a test', VpcId=vpc_id)
    sec_group_id = sec_group['GroupId']

    ec2_client.authorize_security_group_ingress(
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

#Connect boto3 ec2 client to AWS
ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )

#Get vpc_id in AWS
vpc = ec2_client.describe_vpcs()
vpc_id = vpc.get('Vpcs', [{}])[0].get('VpcId', '')
print('VPC is %s' %(vpc_id))

#Get subnet_id in vpc
subnet = ec2_client.describe_subnets(
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

security_group_id = create_security_group(ec2_client,'TestSG',vpc_id)

create_key_pair(ec2_client,key_pair_name)

ec2_instance_id = create_ec2_instance(ec2_client,image_id,instance_type,instance_name,key_pair_name,security_group_id)
