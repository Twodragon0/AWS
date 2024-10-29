import requests
import json
import boto3
from itertools import islice

# Initialize boto3 client for EC2
ec2_client = boto3.client('ec2', region_name='ap-northeast-2')

# JSON URL
url = "https://s3.amazonaws.com/okta-ip-ranges/ip_ranges.json"

# Fetch and parse JSON
response = requests.get(url)
data = response.json()

# Extract 'us_cell_14' IP ranges
us_cell_14_ips = data.get("us_cell_14", {}).get("ip_ranges", [])

# Function to split IPs into chunks of 60
def chunked_list(data, chunk_size=60):
    it = iter(data)
    while True:
        chunk = list(islice(it, chunk_size))
        if not chunk:
            break
        yield chunk

# Split IPs into 60-IP chunks
ip_chunks = list(chunked_list(us_cell_14_ips))

# Create prefix lists and corresponding security groups with a 1:1 relationship
sg_prefix = "SG-OKTA-IP-US-CELL-14"
pl_prefix = "pl-us-cell-14"
vpc_id = "vpc-xx"  # Replace with your actual VPC ID

for idx, chunk in enumerate(ip_chunks, 1):
    # Create a managed prefix list
    response = ec2_client.create_managed_prefix_list(
        PrefixListName=f"{pl_prefix}-{idx}",
        AddressFamily="IPv4",
        MaxEntries=len(chunk),
        Entries=[{"Cidr": ip} for ip in chunk]
    )
    prefix_list_id = response['PrefixList']['PrefixListId']
    print(f"Created Prefix List {prefix_list_id} with {len(chunk)} IPs")

    # Create a security group for each prefix list
    security_group = ec2_client.create_security_group(
        GroupName=f"{sg_prefix}-{idx}",
        Description=f"Security group for {pl_prefix}-{idx}",
        VpcId=vpc_id
    )
    security_group_id = security_group['GroupId']
    print(f"Created Security Group {security_group_id}")

    # Add an inbound rule to the security group for port 443 with the prefix list
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'PrefixListIds': [{'PrefixListId': prefix_list_id}]
            }
        ]
    )
    print(f"Added rule for Prefix List {prefix_list_id} to Security Group {security_group_id}")
