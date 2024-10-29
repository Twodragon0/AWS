import requests
import json
from itertools import islice

# JSON URL
url = "https://s3.amazonaws.com/okta-ip-ranges/ip_ranges.json"

# Fetch and parse JSON
response = requests.get(url)
data = response.json()

# Extract 'us_cell_14' IP ranges
us_cell_14_ips = data.get("us_cell_14", {}).get("ip_ranges", [])

# Function to split IPs into chunks of 60 (AWS limit for prefix list entries)
def chunked_list(data, chunk_size=60):
    it = iter(data)
    while True:
        chunk = list(islice(it, chunk_size))
        if not chunk:
            break
        yield chunk

# Split IPs into 60-IP chunks
ip_chunks = list(chunked_list(us_cell_14_ips))

# Generate JSON structure for AWS VPC prefix lists
for idx, chunk in enumerate(ip_chunks, 1):
    prefix_list = [{"Cidr": ip} for ip in chunk]
    filename = f"aws_prefix_list_{idx}.json"
    with open(filename, "w") as f:
        json.dump(prefix_list, f, indent=4)
    print(f"Prefix list saved as {filename}")
