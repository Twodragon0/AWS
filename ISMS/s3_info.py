import boto3
import csv
from botocore.exceptions import ClientError

# Boto3 클라이언트 생성
s3_client = boto3.client('s3')
# CSV 파일 생성
with open('s3_buckets_info.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["BucketName", "Access", "Location", "Purpose"])
    
    # S3 버킷 리스트 조회
    response = s3_client.list_buckets()
    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        
        try:
            # 버킷 정책 상태 조회 시도
            bucket_policy_status_resp = s3_client.get_bucket_policy_status(Bucket=bucket_name)
            is_public = bucket_policy_status_resp['PolicyStatus']['IsPublic']
            access = 'Public' if is_public else 'Bucket and objects not public'
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucketPolicy':
                access = 'Bucket and objects not public'
            else:
                raise  # 다른 ClientError 발생 시 예외를 다시 발생시킴
            
            # 버킷 ACL 조회
            acl_resp = s3_client.get_bucket_acl(Bucket=bucket_name)
            for grant in acl_resp['Grants']:
                if 'URI' in grant['Grantee'] and grant['Grantee']['URI'] in ['http://acs.amazonaws.com/groups/global/AllUsers', 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers']:
                    access = 'Objects can be public'
                    break
        
        # 버킷 위치 조회
        location_resp = s3_client.get_bucket_location(Bucket=bucket_name)
        location = location_resp.get('LocationConstraint', 'us-east-1') if location_resp['LocationConstraint'] else 'us-east-1'
        
        # 버킷 용도는 사용자 입력 필요
        purpose = 'General'  # 실제 사용 시 적절한 값을 설정해야 함
        
        # CSV 파일에 기록
        writer.writerow([bucket_name, access, location, purpose])
