import boto3
import os
from paramiko import RSAKey
import paramiko

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']
region = 'eu-central-1'
image_id = 'ami-0ebe657bc328d4e82'
instance_type = 't2.micro'
username = 'ec2-user'
key_pair_name = 'mykey'
instance_name = 'myec2'
volume_name = 'myvolume'

def create_ec2_instance(ec2_client,ec2_resource,image_id,instance_type,instance_name,key_pair_name,sg_id):
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
                    return

    # Instance was not found, create it
    print('Creating instance. Please wait.')
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

def generate_keypair(key_pair_name):
    # generating private key
    prv = RSAKey.generate(bits=2048)
    prv.write_private_key_file(key_pair_name)

    # generating public key
    pub = RSAKey(filename=key_pair_name)
    with open("%s.pub" % key_pair_name, "w") as f:
        f.write("%s %s" % (pub.get_name(), pub.get_base64()))
    
    #Read public key
    fp = open(os.path.expanduser('./%s.pub' % key_pair_name))
    pub_key = fp.read()
    fp.close()
    return pub_key


def create_key_pair(ec2_client,key_pair_name):
    
    if not ec2_client.describe_key_pairs(Filters=[{'Name': 'key-name','Values': [key_pair_name]}])['KeyPairs']:        
        pub_key = generate_keypair(key_pair_name)
        ec2_client.import_key_pair(KeyName=key_pair_name,PublicKeyMaterial=pub_key)
        return
    print('Keys was generated previously. If the keys have been lost then you need recreate all.')

def create_security_group(ec2_client,groupName,vpc_id):
    for sec_group in ec2_client.describe_security_groups()['SecurityGroups']:
        if sec_group['GroupName'] == groupName:
            sec_group_id = sec_group['GroupId']
            print('Security group id is %s' % sec_group_id)
            return (sec_group_id)

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
    print('Security group id is %s' % sec_group_id)
    return(sec_group_id)

def create_attach_ebs(ec2_resource,ec2_client,instance_availability_zone,ec2_instance_id,volume_name):
    volumes = ec2_client.describe_volumes(Filters=[{'Name': 'tag:Name','Values': [volume_name]}])['Volumes']
    
    #Check is volume was create previously
    if volumes:
        for volume in volumes:
            for attach in volume['Attachments']:
                if attach['InstanceId']==ec2_instance_id:
                    print('Volume was created previously and attached to instance')
                    return
            if volume['State']!='in-use':
                print('Volume was created previously but not attached. Please wait.')
                volume_id=volume['VolumeId']
                volume=ec2_resource.Volume(volume_id)
                volume.attach_to_instance(Device='/dev/xvdh',InstanceId=ec2_instance_id)
                ec2_client.get_waiter('volume_in_use').wait(VolumeIds=[volume_id])
                return
    
    print('Creating volume. Please wait.')
    create_response=ec2_client.create_volume(AvailabilityZone=instance_availability_zone,Size=1,VolumeType='standard',TagSpecifications=[{'ResourceType': 'volume','Tags': [{'Key': 'Name','Value': volume_name}]}])
    volume_id=create_response['VolumeId']
    volume=ec2_resource.Volume(volume_id)
    ec2_client.get_waiter('volume_available').wait(VolumeIds=[volume_id])    
    volume.attach_to_instance(Device='/dev/xvdh',InstanceId=ec2_instance_id)
    ec2_client.get_waiter('volume_in_use').wait(VolumeIds=[volume_id])


def ssh_instance(ec2_instance_public_ip,key_pair_name,username):
    if not os.path.exists("./%s" % key_pair_name):
        print('Private key in current folder not found! Can`t ssh to instance.')
        return    
    host_address = ec2_instance_public_ip
    k = paramiko.RSAKey.from_private_key_file("./%s" % key_pair_name)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("connecting")
    c.connect(hostname=host_address, username=username, pkey=k)
    print("connected")
    commands = ["sudo -S lsblk","sudo -S mkfs.ext4 /dev/xvdh", "sudo -S mkdir /data", "sudo -S mount /dev/xvdh /data"]
    for command in commands:
        print("Executing {}".format(command))        
        stdin, stdout, stderr = c.exec_command(command)
        print(stdout.read())
        print("Errors")
        print(stderr.read())
    c.close()

def get_info(ec2_client,instance_name):
    instances = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name','Values': [ instance_name ]}])
    if instances['Reservations']:
        for reservations in instances['Reservations']:
            for instance in reservations['Instances']:
                if instance['State']['Name']=='running' or instance['State']['Name']=='pending':
                    return instance['InstanceId'], instance['PublicIpAddress'], instance['Placement']['AvailabilityZone']

#Connect boto3 ec2 client to AWS
ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )
    
ec2_resource = boto3.resource(
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

create_ec2_instance(ec2_client,ec2_resource,image_id,instance_type,instance_name,key_pair_name,security_group_id)

ec2_instance_id, ec2_instance_public_ip, instance_availability_zone = get_info(ec2_client,instance_name)

create_attach_ebs(ec2_resource,ec2_client,instance_availability_zone,ec2_instance_id,volume_name)

ssh_instance(ec2_instance_public_ip,key_pair_name,username)