import boto3
import csv

YOUR_REGION = 'ap-northeast-2'

# Create an EC2 client
ec2 = boto3.client('ec2', region_name=YOUR_REGION)

# Retrieve all instances (both running and stopped)
instances = ec2.describe_instances()

# Create a list to hold the instance details
instance_details = []

# Append the details of each instance to the list
for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        name = ''
        for tag in instance.get('Tags', []):
            if tag['Key'] == 'Name':
                name = tag['Value']
                break

        private_ip_address = instance.get('PrivateIpAddress', '')
        public_ip_address = instance.get('PublicIpAddress', '')

        # Get the Network Interface information
        network_interfaces = instance.get('NetworkInterfaces', [])
        for network_interface in network_interfaces:
            network_interface_id = network_interface.get('NetworkInterfaceId', '')
            instance_details.append({
                'Name': name,
                'Instance ID': instance_id,
                'Private IP': private_ip_address,
                'Public IP': public_ip_address,
                'Network Interface ID': network_interface_id
            })

# Write the instance details to a CSV file
with open('instance_details.csv', 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['Name', 'Instance ID', 'Private IP', 'Public IP', 'Network Interface ID'])
    writer.writeheader()
    for instance in instance_details:
        writer.writerow(instance)
