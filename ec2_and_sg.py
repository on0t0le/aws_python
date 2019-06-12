import logging
import boto3
from botocore.exceptions import ClientError
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']

def create_sg(ec2):
    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

    try:
        response = ec2.create_security_group(GroupName='TestPySG',
                                             Description='Test description',
                                             VpcId=vpc_id)
        security_group_id = response['GroupId']
        print('Security Group Created %s in vpc %s.' %
              (security_group_id, vpc_id))

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
    return security_group_id


def create_ec2_instance(ec2_client, image_id, instance_type, keypair_name):

    sg_id = create_sg(ec2_client)
    if sg_id is not None:
        try:
            response = ec2_client.run_instances(ImageId=image_id,
                                                InstanceType=instance_type,
                                                KeyName=keypair_name,
                                                MinCount=1,
                                                MaxCount=1,
                                                NetworkInterfaces=[{'DeviceIndex': 0,'AssociatePublicIpAddress': True, 'Groups': [sg_id]}])
        except ClientError as e:
            logging.error(e)
            return None
    return response['Instances'][0]


def main():
    """Exercise create_ec2_instance()"""

    # Assign these values before running the program
    image_id = 'ami-0ebe657bc328d4e82'
    instance_type = 't2.micro'
    keypair_name = 'aperture-web1'
    access_key_id = access_key_id
    secret_access_key = secret_access_key
    region = 'eu-central-1'    

    # Set up logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(asctime)s: %(message)s')

    ec2 = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )

    # Provision and launch the EC2 instance
    instance_info = create_ec2_instance(ec2, image_id, instance_type, keypair_name)
    if instance_info is not None:
        print('Launched EC2 Instance %s in vpc %s.' % (instance_info["InstanceId"], instance_info["VpcId"]))
        #print('Security group %s . Current State: %s.' % (instance_info["SecurityGroups"]["GroupName"], instance_info["State"]["Name"]))      


if __name__ == '__main__':
    main()
