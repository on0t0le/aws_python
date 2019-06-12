import boto3
import os
from paramiko import RSAKey
import paramiko

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']
region = 'eu-central-1'
image_id = 'ami-0ebe657bc328d4e82'
instance_type = 't2.micro'
key_pair_name = 'testkeypy'
instance_name = 'TestEC2'
username = 'ec2-user'

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
                    return instance['InstanceId'], instance['PublicIpAddress']

    # Instance was not found, create it

    instances = ec2_client.run_instances(**params)

    instance_id = instances['Instances'][0]['InstanceId']
    instance_public_ip = instances['Instances'][0]['PublicIpAddress']

    #Wait instance running state
    run_waiter = ec2_client.get_waiter('instance_running')
    run_waiter.wait(InstanceIds=[instance_id])
    print('Instance %s is running, but NOT all checks' %(instance_id))

    #Wait instance OK state
    ok_waiter = ec2_client.get_waiter('instance_status_ok')
    ok_waiter.wait(InstanceIds=[instance_id])
    print('Instance %s is running succesfully!' %(instance_id))

    return instance_id, instance_public_ip

def generate_keypair(key_pair_name):
    filename = key_pair_name

    # generating private key
    prv = RSAKey.generate(bits=2048)
    prv.write_private_key_file(filename)

    # generating public key
    pub = RSAKey(filename=filename)
    with open("%s.pub" % filename, "w") as f:
        f.write("%s %s" % (pub.get_name(), pub.get_base64()))
    
    #Read public key
    fp = open(os.path.expanduser('./%s.pub' % filename))
    pub_key = fp.read()
    fp.close()
    return pub_key


def create_key_pair(ec2_client,key_pair_name):
    
    if not ec2_client.describe_key_pairs(Filters=[{'Name': 'key-name','Values': [key_pair_name]}])['KeyPairs']:        
        pub_key = generate_keypair(key_pair_name)
        ec2_client.import_key_pair(KeyName=key_pair_name,PublicKeyMaterial=pub_key)
    print('Keys was generated previously. If the keys have been lost then you need recreate all.')

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

def ssh_instance(host_address,key_pair_name,username):
    host_address = host_address
    k = paramiko.RSAKey.from_private_key_file("./%s" % key_pair_name)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("connecting")
    c.connect(hostname=host_address, username=username, pkey=k)
    print("connected")
    commands = ["ls /home/", "ls /tmp", "sudo -S mkdir /tmp/test"]
    for command in commands:
        #print("Executing {}".format(command))
        stdin, stdout, stderr = c.exec_command(command)
        print(stdout.read())
        print("Errors")
        print(stderr.read())
    # stdin, stdout, stderr = c.exec_command('sudo -S whoami')
    # print(stdout.read())
    c.close()

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

ec2_instance_id, ec2_instance_public_ip = create_ec2_instance(ec2_client,image_id,instance_type,instance_name,key_pair_name,security_group_id)

ssh_instance(ec2_instance_public_ip,key_pair_name,username)