#!/bin/bash

# Download the AWS IP ranges JSON file
curl https://ip-ranges.amazonaws.com/ip-ranges.json -o ip-ranges.json

# Extract S3 service IP ranges for the us-east-1 region using jq
s3_us_east_1=$(cat ip-ranges.json | jq -r '
  .prefixes[] |
  select(.region == "us-east-1" and .service == "S3") |
  .ip_prefix')

# Extract S3 service IP ranges for the us-east-2 region using jq
s3_us_east_2=$(cat ip-ranges.json | jq -r '
  .prefixes[] |
  select(.region == "us-east-2" and .service == "S3") |
  .ip_prefix')

# Extract S3 service IP ranges for the ap-northeast-2 region using jq
s3_ap_northeast_2=$(cat ip-ranges.json | jq -r '
  .prefixes[] |
  select(.region == "ap-northeast-2" and .service == "S3") |
  .ip_prefix')

# Print the extracted IP ranges for us-east-1
echo "us-east-1 S3 IP ranges:"
echo "$s3_us_east_1"
echo

# Print the extracted IP ranges for us-east-2
echo "us-east-2 S3 IP ranges:"
echo "$s3_us_east_2"
echo

# Print the extracted IP ranges for ap-northeast-2
echo "ap-northeast-2 S3 IP ranges:"
echo "$s3_ap_northeast_2"
