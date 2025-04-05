import json
import boto3
import csv

def get_bucket_acl(client, bucket):
    try:
        response = client.get_bucket_acl(Bucket=bucket)
        output = "-"
        for grant in response["Grants"]:
            try:
                if "AllUsers" in grant["Grantee"]["URI"]:
                    output = grant["Permission"]
            except Exception as e:
                continue
        return output
    except Exception as e:
        return "-"

def get_bucket_encryption(client, bucket):
    try:
        response = client.get_bucket_encryption(Bucket=bucket)
        return "Good"
    except Exception as e:
        return "Weak"

def get_bucket_logging(client, bucket):
    try:
        response = client.get_bucket_logging(Bucket=bucket)
        return "Good"
    except Exception as e:
        return "Weak"

def get_bucket_policy(client, bucket):
    try:
        response = client.get_bucket_policy(Bucket=bucket)
        return json.dumps(response["Policy"]).replace('"', "'")
    except Exception as e:
        return "-"

def get_public_access_block(client, bucket):
    try:
        response = client.get_public_access_block(Bucket=bucket)
        check = response["PublicAccessBlockConfiguration"]
        return check["BlockPublicAcls"] and check["IgnorePublicAcls"] and check["BlockPublicPolicy"] and check["RestrictPublicBuckets"]
    except Exception as e:
        return "Unknown"

def get_bucket_encryption_rules(client, bucket):
    try:
        response = client.get_bucket_encryption(Bucket=bucket)
        return json.dumps(response["ServerSideEncryptionConfiguration"]["Rules"])
    except Exception as e:
        return "-"

if __name__ == "__main__":
    client = boto3.client('s3', region_name="ap-northeast-2")
    response = client.list_buckets()

    with open('s3_bucket_info.csv', 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Name', 'Bucket Encryption', 'Bucket Logging', 'ACL', 'Bucket Policy', 'Public Access Block', 'Encryption Rules'])

        for bucket in response["Buckets"]:
            bucket_name = bucket["Name"]
            bucket_encryption = get_bucket_encryption(client, bucket_name)
            bucket_logging = get_bucket_logging(client, bucket_name)
            bucket_acl = get_bucket_acl(client, bucket_name)
            bucket_policy = get_bucket_policy(client, bucket_name)
            public_access_block = get_public_access_block(client, bucket_name)
            encryption_rules = get_bucket_encryption_rules(client, bucket_name)

            writer.writerow([bucket_name, bucket_encryption, bucket_logging, bucket_acl, bucket_policy, public_access_block, encryption_rules])
