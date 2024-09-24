import boto3
import csv
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from botocore.exceptions import ClientError
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Drive 인증을 위한 서비스 계정 JSON 파일 경로
SERVICE_ACCOUNT_FILE = '/Users/<username>/Desktop/1.json'

# Google Drive와 연결 설정
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)

# Boto3 클라이언트 생성
ec2_client = boto3.client('ec2')
s3_client = boto3.client('s3')

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

# S3 버킷 정보 조회
s3_response = s3_client.list_buckets()

# S3 버킷 정보 저장을 위한 리스트
s3_data = []

# S3 버킷 정보 추출 및 리스트에 추가
for bucket in s3_response['Buckets']:
    bucket_name = bucket['Name']
    try:
        bucket_policy_status_resp = s3_client.get_bucket_policy_status(Bucket=bucket_name)
        is_public = bucket_policy_status_resp['PolicyStatus']['IsPublic']
        access = 'Public' if is_public else 'Bucket and objects not public'
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucketPolicy':
            access = 'Bucket and objects not public'
        else:
            raise
    
    location_resp = s3_client.get_bucket_location(Bucket=bucket_name)
    location = location_resp.get('LocationConstraint', 'us-east-1') if location_resp['LocationConstraint'] else 'us-east-1'
    purpose = 'General'
    s3_data.append([bucket_name, access, location, purpose])

# 데이터프레임으로 변환
ec2_df = pd.DataFrame(ec2_data, columns=['HostName', 'Instance ID', 'Spec', 'OS', 'Version', 'Availability Zone', 'Public IP', 'Private IP', 'Usage', 'Status'])
s3_df = pd.DataFrame(s3_data, columns=['BucketName', 'Access', 'Location', 'Purpose'])

# XLSX 파일로 변환
with pd.ExcelWriter('aws_assets_isms_p.xlsx', engine='openpyxl') as writer:
    ec2_df.to_excel(writer, sheet_name='EC2 Instances', index=False)
    s3_df.to_excel(writer, sheet_name='S3 Buckets', index=False)

# Google Drive에 업로드
sh = client.create('AWS Assets ISMS-P')  # 스프레드시트 생성
worksheet_ec2 = sh.add_worksheet(title='EC2 Instances', rows="100", cols="20")
worksheet_s3 = sh.add_worksheet(title='S3 Buckets', rows="100", cols="20")

# EC2 인스턴스 데이터를 Google Drive에 추가
for r_idx, row in enumerate(dataframe_to_rows(ec2_df, index=False, header=True)):
    worksheet_ec2.insert_row(row, r_idx + 1)

# S3 버킷 데이터를 Google Drive에 추가
for r_idx, row in enumerate(dataframe_to_rows(s3_df, index=False, header=True)):
    worksheet_s3.insert_row(row, r_idx + 1)

print("Google Drive에 업로드 완료.")
