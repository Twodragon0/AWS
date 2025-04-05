import boto3
import csv
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from botocore.exceptions import ClientError
from oauth2client.service_account import ServiceAccountCredentials
import json


# Boto3 클라이언트 생성
ec2_client = boto3.client('ec2')
s3_client = boto3.client('s3')
ecr_client = boto3.client('ecr', region_name='ap-northeast-2')  # 리전 설정
route53_client = boto3.client('route53')
rds_client = boto3.client('rds')
cloudfront_client = boto3.client('cloudfront')
lambda_client = boto3.client('lambda')
iam_client = boto3.client('iam')

# EC2 인스턴스 정보 조회
ec2_response = ec2_client.describe_instances()

# EC2 인스턴스 정보 저장을 위한 리스트
ec2_data = []

# EC2 인스턴스 정보 추출 및 리스트에 추가
for reservation in ec2_response['Reservations']:
    for instance in reservation['Instances']:
        host_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), None)
        usage = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Usage'), None)
        instance_id = instance['InstanceId']
        spec = instance['InstanceType']
        os = instance.get('Platform', 'Linux/UNIX')
        version = instance.get('ImageId', 'N/A')
        availability_zone = instance['Placement']['AvailabilityZone']
        public_ip = instance.get('PublicIpAddress', 'N/A')
        private_ip = instance.get('PrivateIpAddress', 'N/A')
        status = instance['State']['Name']
        ec2_data.append([host_name, instance_id, spec, os, version, availability_zone, public_ip, private_ip, usage, status])

# S3 자산 정보 수집 함수들

def get_bucket_acl(client, bucket):
    """버킷 ACL 정보 조회"""
    try:
        response = client.get_bucket_acl(Bucket=bucket)
        acl_info = []
        for grant in response['Grants']:
            grantee = grant['Grantee']
            permission = grant['Permission']
            acl_info.append(f"{grantee.get('Type')}: {permission}")
        return ', '.join(acl_info)
    except ClientError as e:
        return f"Error: {str(e)}"

def get_bucket_encryption(client, bucket):
    """버킷 암호화 정보 조회"""
    try:
        response = client.get_bucket_encryption(Bucket=bucket)
        encryption_rules = response['ServerSideEncryptionConfiguration']['Rules']
        return json.dumps(encryption_rules, indent=2)
    except ClientError as e:
        return f"Error: {str(e)}"

def get_bucket_logging(client, bucket):
    """버킷 로깅 설정 정보 조회"""
    try:
        response = client.get_bucket_logging(Bucket=bucket)
        logging_info = response.get('LoggingEnabled', {})
        if logging_info:
            return f"TargetBucket: {logging_info.get('TargetBucket')}, TargetPrefix: {logging_info.get('TargetPrefix')}"
        else:
            return "Logging not enabled"
    except ClientError as e:
        return f"Error: {str(e)}"

def get_bucket_policy(client, bucket):
    """버킷 정책 조회"""
    try:
        response = client.get_bucket_policy(Bucket=bucket)
        return json.dumps(json.loads(response['Policy']), indent=2)
    except ClientError as e:
        return f"Error: {str(e)}"

def get_public_access_block(client, bucket):
    """버킷 퍼블릭 액세스 차단 정보 조회"""
    try:
        response = client.get_public_access_block(Bucket=bucket)
        block_config = response['PublicAccessBlockConfiguration']
        return json.dumps(block_config, indent=2)
    except ClientError as e:
        return f"Error: {str(e)}"

# S3 버킷 정보 조회 및 상세 정보 수집
s3_response = s3_client.list_buckets()

s3_data = []
for bucket in s3_response['Buckets']:
    bucket_name = bucket['Name']
    bucket_acl = get_bucket_acl(s3_client, bucket_name)
    bucket_encryption = get_bucket_encryption(s3_client, bucket_name)
    bucket_logging = get_bucket_logging(s3_client, bucket_name)
    bucket_policy = get_bucket_policy(s3_client, bucket_name)
    public_access_block = get_public_access_block(s3_client, bucket_name)

    s3_data.append([bucket_name, bucket_acl, bucket_encryption, bucket_logging, bucket_policy, public_access_block])

# ECR 리포지토리 정보 조회 함수
def get_ecr_repositories():
    repositories = []
    response = ecr_client.describe_repositories()
    
    while True:
        repositories.extend(response['repositories'])
        if 'nextToken' in response:
            response = ecr_client.describe_repositories(nextToken=response['nextToken'])
        else:
            break
    return repositories

# ECR 리포지토리 자산 정보 수집 함수
def get_ecr_asset_info():
    ecr_data = []
    repositories = get_ecr_repositories()

    for repo in repositories:
        repository_name = repo['repositoryName']
        repository_uri = repo['repositoryUri']
        created_at = repo['createdAt'].strftime("%Y-%m-%d %H:%M:%S")
        image_scanning = repo['imageScanningConfiguration']['scanOnPush']
        image_tag_mutability = repo['imageTagMutability']
        lifecycle_policy = "Enabled" if 'lifecyclePolicy' in repo else "Disabled"
        
        ecr_data.append([
            repository_name,
            repository_uri,
            created_at,
            image_scanning,
            image_tag_mutability,
            lifecycle_policy
        ])
    return ecr_data


# IAM 자산 정보 수집 클래스
class imds:
    def __init__(self):
        # Boto3 클라이언트를 사용하여 IAM API 호출
        self.iam_client = boto3.client('iam')

    def getIamRoleList(self):
        """모든 IAM 역할을 가져옵니다."""
        iam_role_list = []
        paginator = self.iam_client.get_paginator('list_roles')
        for page in paginator.paginate():
            for role in page['Roles']:
                iam_role_list.append(role['RoleName'])
        return iam_role_list

    def getPolicyInlineList(self, iam_role):
        """특정 IAM 역할의 인라인 정책을 가져옵니다."""
        inline_policies = []
        paginator = self.iam_client.get_paginator('list_role_policies')
        for page in paginator.paginate(RoleName=iam_role):
            inline_policies.extend(page['PolicyNames'])
        return inline_policies

    def getPolicyManagedList(self, iam_role):
        """특정 IAM 역할의 관리형 정책을 가져옵니다."""
        managed_policies = []
        paginator = self.iam_client.get_paginator('list_attached_role_policies')
        for page in paginator.paginate(RoleName=iam_role):
            managed_policies.extend(page['AttachedPolicies'])
        return managed_policies

    def getPolicyDocument(self, iam_role, policy_name, policy_arn=None, policy_type='inline'):
        """특정 IAM 역할의 인라인 또는 관리형 정책 문서를 가져옵니다."""
        if policy_type == 'inline':
            response = self.iam_client.get_role_policy(RoleName=iam_role, PolicyName=policy_name)
            return response['PolicyDocument']
        else:
            # 관리형 정책은 ARN을 통해 가져옴
            response = self.iam_client.get_policy(PolicyArn=policy_arn)
            default_version_id = response['Policy']['DefaultVersionId']
            version = self.iam_client.get_policy_version(PolicyArn=policy_arn, VersionId=default_version_id)
            return version['PolicyVersion']['Document']

# IAM 자산 수집 실행
tool = imds()
iam_role_list = tool.getIamRoleList()
iam_data = []

# 각 IAM 역할에 대해 정책 정보를 수집
for iam_role in iam_role_list:
    print(f"Collecting policies for IAM role: {iam_role}")
    
    # 인라인 정책 가져오기
    inline_policies = tool.getPolicyInlineList(iam_role)
    for policy_name in inline_policies:
        policy_document = tool.getPolicyDocument(iam_role, policy_name, policy_type='inline')
        iam_data.append([iam_role, policy_name, 'inline', json.dumps(policy_document)])

    # 관리형 정책 가져오기
    managed_policies = tool.getPolicyManagedList(iam_role)
    for policy in managed_policies:
        policy_name = policy['PolicyName']
        policy_arn = policy['PolicyArn']  # 관리형 정책의 ARN을 가져옴
        policy_document = tool.getPolicyDocument(iam_role, policy_name, policy_arn=policy_arn, policy_type='managed')
        iam_data.append([iam_role, policy_name, 'managed', json.dumps(policy_document)])


# Route 53 자산 정보 수집 함수
def get_hosted_zones():
    """모든 Route 53 호스티드 존의 정보를 가져옵니다."""
    hosted_zones = route53_client.list_hosted_zones()
    zones_info = [(zone['Id'].split('/')[-1], zone['Name']) for zone in hosted_zones['HostedZones']]
    return zones_info

def get_records_by_zone(zone_id):
    """주어진 호스티드 존 ID에 대한 모든 레코드 세트 정보를 가져옵니다."""
    paginator = route53_client.get_paginator('list_resource_record_sets')
    page_iterator = paginator.paginate(HostedZoneId=zone_id)
    
    records_info = []
    for page in page_iterator:
        for record in page['ResourceRecordSets']:
            record_values = [value['Value'] for value in record.get('ResourceRecords', [])]
            alias_target = record.get('AliasTarget', {})
            record_info = {
                'Name': record['Name'],
                'Type': record['Type'],
                'TTL': record.get('TTL', 'N/A'),
                'RoutingPolicy': record.get('RoutingPolicy', 'N/A'),
                'Values': ', '.join(record_values) if record_values else 'N/A',
                'AliasDNSName': alias_target.get('DNSName', 'N/A'),
                'AliasHostedZoneId': alias_target.get('HostedZoneId', 'N/A')
            }
            records_info.append(record_info)
    return records_info

def get_route53_asset_info():
    """Route 53 호스티드 존 및 해당 레코드 세트 정보를 수집합니다."""
    zones_info = get_hosted_zones()
    route53_data = []
    for zone_id, zone_name in zones_info:
        records = get_records_by_zone(zone_id)
        for record in records:
            record['HostedZoneId'] = zone_id
            record['HostedZoneName'] = zone_name
            route53_data.append(record)
    return route53_data

# RDS 자산 정보 수집 함수
def get_rds_instances():
    """모든 RDS 인스턴스의 정보를 가져옵니다."""
    instances = rds_client.describe_db_instances()['DBInstances']
    rds_info = []
    for instance in instances:
        rds_info.append({
            'DBInstanceIdentifier': instance['DBInstanceIdentifier'],
            'DBInstanceClass': instance['DBInstanceClass'],
            'Engine': instance['Engine'],
            'EngineVersion': instance['EngineVersion'],
            'AvailabilityZone': instance['AvailabilityZone'],
            'DBInstanceStatus': instance['DBInstanceStatus'],
            'Endpoint': instance.get('Endpoint', {}).get('Address', 'N/A')
        })
    return rds_info

# CloudFront 자산 정보 수집 함수
def get_cloudfront_distributions():
    """모든 CloudFront 배포 정보를 가져옵니다."""
    distributions = cloudfront_client.list_distributions().get('DistributionList', {}).get('Items', [])
    cloudfront_info = []
    for dist in distributions:
        cloudfront_info.append({
            'Id': dist['Id'],
            'DomainName': dist['DomainName'],
            'Status': dist['Status'],
            'Enabled': dist['Enabled'],
            'OriginDomainName': dist['Origins']['Items'][0]['DomainName'],
            'Comment': dist['Comment']
        })
    return cloudfront_info

# Lambda 자산 정보 수집 함수
def get_lambda_functions():
    """모든 Lambda 함수의 정보를 가져옵니다."""
    functions = lambda_client.list_functions()['Functions']
    lambda_info = []
    for func in functions:
        lambda_info.append({
            'FunctionName': func['FunctionName'],
            'Runtime': func['Runtime'],
            'Handler': func['Handler'],
            'Timeout': func['Timeout'],
            'MemorySize': func['MemorySize'],
            'LastModified': func['LastModified']
        })
    return lambda_info

# 자산 수집 실행
ecr_assets = get_ecr_asset_info()
route53_assets = get_route53_asset_info()
rds_assets = get_rds_instances()
cloudfront_assets = get_cloudfront_distributions()
lambda_assets = get_lambda_functions()

# 데이터프레임으로 변환
ec2_df = pd.DataFrame(ec2_data, columns=['HostName', 'Instance ID', 'Spec', 'OS', 'Version', 'Availability Zone', 'Public IP', 'Private IP', 'Usage', 'Status'])
s3_df = pd.DataFrame(s3_data, columns=['BucketName', 'ACL', 'Encryption', 'Logging', 'Policy', 'Public Access Block'])
ecr_df = pd.DataFrame(ecr_assets, columns=['Repository Name', 'Repository URI', 'Created At', 'Image Scanning', 'Tag Mutability', 'Lifecycle Policy'])
iam_df = pd.DataFrame(iam_data, columns=['Role Name', 'Policy Name', 'Policy Type', 'Policy Document'])
route53_df = pd.DataFrame(route53_assets, columns=['HostedZoneId', 'HostedZoneName', 'Record Name', 'Record Type', 'TTL'])
rds_df = pd.DataFrame(rds_assets, columns=['DBInstanceIdentifier', 'DBInstanceClass', 'Engine', 'EngineVersion', 'AvailabilityZone', 'DBInstanceStatus', 'Endpoint'])
cloudfront_df = pd.DataFrame(cloudfront_assets, columns=['Id', 'DomainName', 'Status', 'Enabled', 'OriginDomainName'])
lambda_df = pd.DataFrame(lambda_assets, columns=['FunctionName', 'Runtime', 'Handler', 'Timeout', 'MemorySize', 'LastModified'])

# XLSX 파일로 변환
with pd.ExcelWriter('aws_assets_isms_p_v3.xlsx', engine='openpyxl') as writer:
    ec2_df.to_excel(writer, sheet_name='EC2 Instances', index=False)
    s3_df.to_excel(writer, sheet_name='S3 Buckets', index=False)
    ecr_df.to_excel(writer, sheet_name='ECR Repositories', index=False)
    iam_df.to_excel(writer, sheet_name='IAM Roles', index=False)
    route53_df.to_excel(writer, sheet_name='Route53 Records', index=False)
    rds_df.to_excel(writer, sheet_name='RDS Instances', index=False)
    cloudfront_df.to_excel(writer, sheet_name='CloudFront Distributions', index=False)
    lambda_df.to_excel(writer, sheet_name='Lambda Functions', index=False)


# 작업 완료 메시지 출력
print("모든 AWS 자산 정보를 'aws_assets_isms_p_v3.xlsx' 파일로 내보냈습니다.")

