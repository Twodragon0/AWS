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

# Create managed prefix lists with "pl-*" naming convention and store their IDs
prefix_list_ids = []
for idx, chunk in enumerate(ip_chunks, 1):
    response = ec2_client.create_managed_prefix_list(
        PrefixListName=f"pl-us-cell-14-{idx}",
        AddressFamily="IPv4",
        MaxEntries=len(chunk),
        Entries=[{"Cidr": ip} for ip in chunk]
    )
    prefix_list_id = response['PrefixList']['PrefixListId']
    prefix_list_ids.append(prefix_list_id)
    print(f"Created Prefix List {prefix_list_id} with {len(chunk)} IPs")

# Security group prefix and rule limit
sg_prefix = "SG-14"
max_rules_per_sg = 60

# Create and configure security groups as needed
for sg_index, chunk in enumerate(chunked_list(prefix_list_ids, max_rules_per_sg), 1):
    # Create a new security group for each set of 60 prefix lists
    security_group = ec2_client.create_security_group(
        GroupName=f"{sg_prefix}-{sg_index}",
        Description="Security group with prefix lists for Okta us_cell_14",
        VpcId="vpc-xx"
    )
    security_group_id = security_group['GroupId']
    print(f"Created Security Group {security_group_id}")

    # Add inbound rules for port 443 using prefix lists in this security group
    ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 443,
                'ToPort': 443,
                'PrefixListIds': [{'PrefixListId': prefix_list_id} for prefix_list_id in chunk]
            }
        ]
    )
    print(f"Added rules for Prefix Lists to Security Group {security_group_id}")
