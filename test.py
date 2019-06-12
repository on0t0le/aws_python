import logging
import boto3
from botocore.exceptions import ClientError
import os

access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['aws_secret_access_key']

# client = boto3.client(
#     'ec2',
#     aws_access_key_id="AKIAUALX37SZFGIU6NEL",
#     aws_secret_access_key="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",
#     region_name="eu-central-1"
# )

# response = client.describe_instances()
# for reservation in response["Reservations"]:
#     for instance in reservation["Instances"]:
#         # This sample print will output entire Dictionary object
#         print(instance)
#         # This will print will output the value of the Dictionary key 'InstanceId'
#         print(instance["InstanceId"])

def create_ec2_instance(image_id, instance_type, keypair_name, access_key_id, secret_access_key):
    """Provision and launch an EC2 instance

    The method returns without waiting for the instance to reach
    a running state.

    :param image_id: ID of AMI to launch, such as 'ami-XXXX'
    :param instance_type: string, such as 't2.micro'
    :param keypair_name: string, name of the key pair
    :return Dictionary containing information about the instance. If error,
    returns None.
    """

    # Provision and launch the EC2 instance
    #ec2_client = boto3.client('ec2')

    ec2_client = boto3.client(
        'ec2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="eu-central-1"
    )

    try:
        response = ec2_client.run_instances(ImageId=image_id,
                                            InstanceType=instance_type,
                                            KeyName=keypair_name,
                                            MinCount=1,
                                            MaxCount=1)
    except ClientError as e:
        logging.error(e)
        return None
    return response['Instances'][0]


def main(access_key_id, secret_access_key):
    """Exercise create_ec2_instance()"""

    # Assign these values before running the program
    image_id = 'ami-0ebe657bc328d4e82'
    instance_type = 't2.micro'
    keypair_name = 'aperture-web1'

    # Set up logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(asctime)s: %(message)s')

    # Provision and launch the EC2 instance
    instance_info = create_ec2_instance(image_id, instance_type, keypair_name, access_key_id, secret_access_key)
    if instance_info is not None:
        logging.info(f'Launched EC2 Instance {instance_info["InstanceId"]}')
        logging.info(f'    VPC ID: {instance_info["VpcId"]}')
        logging.info(f'    Private IP Address: {instance_info["PrivateIpAddress"]}')
        logging.info(f'    Current State: {instance_info["State"]["Name"]}')


if __name__ == '__main__':
    main(access_key_id, secret_access_key)