import boto3
import pandas as pd
import json
import os
from datetime import datetime

# AWS SDK 클라이언트
ec2_client = boto3.client('ec2', region_name='ap-northeast-2')
elbv2_client = boto3.client('elbv2')
rds_client = boto3.client('rds')
cloudfront_client = boto3.client('cloudfront')
sns_client = boto3.client('sns')
s3_client = boto3.client('s3')

# 환경 변수
EC2_SG_ID = os.getenv('EC2_SG_ID', 'sg-xxx')
VPC_ENDPOINT_SG_ID = os.getenv('VPC_ENDPOINT_SG_ID', 'sg-xxx')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')
S3_BUCKET = os.getenv('S3_BUCKET', 'your-s3-bucket')

def send_sns_message(message):
    """SNS로 메시지 전송"""
    if not SNS_TOPIC_ARN:
        print("SNS Topic ARN이 설정되지 않았습니다.")
        return
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="AWS Monitor Alert"
    )

def lambda_handler(event, context):
    try:
        # EC2 인스턴스 필터링
        ec2_instances = get_ec2_instances()

        # 모든 ALB 정보 가져오기
        albs = get_all_albs()

        # EC2 네트워크 인터페이스 정보 가져오기
        network_interfaces = get_network_interface_info()

        # RDS 인스턴스 정보 가져오기
        rds_instances = get_rds_public_ips()

        # CloudFront 배포 정보 가져오기
        cloudfront_distributions = get_cloudfront_info()

        # 엑셀 파일로 저장할 데이터를 구성
        excel_data = []

        # ALB 정보 추가 및 IP 변경 모니터링
        for alb in albs:
            alb_name = alb['LoadBalancerName']
            alb_scheme = alb['Scheme']
            current_ips = get_alb_ips(alb)

            # ALB 타입에 따라 Public 또는 Private IP로 구분
            alb_type = "Public" if alb_scheme == "internet-facing" else "Private"

            # 엑셀 저장을 위한 데이터 구성
            for ip in current_ips:
                excel_data.append({
                    'Name': alb_name,
                    'Type': alb_type,
                    'Public IP': ip,
                    'Public DNS': 'N/A',
                    'Security Group ID': 'N/A'
                })

            # IP 변경 알림
            message = (f"리소스 '{alb_name}'의 IP 주소가 변경되었습니다! ({alb_type})\n"
                       f"새로운 IP: {current_ips}")
            send_sns_message(message)
            print(message)

        # EC2 네트워크 인터페이스 정보 추가
        for network_interface in network_interfaces:
            excel_data.append(network_interface)

        # RDS 인스턴스 정보 추가
        for rds_instance in rds_instances:
            excel_data.append(rds_instance)

        # CloudFront 배포 정보 추가
        for cloudfront in cloudfront_distributions:
            excel_data.append(cloudfront)

        # EC2 인스턴스 정보 추가
        for instance in ec2_instances:
            excel_data.append(instance)

        # 모든 데이터를 엑셀 파일에 저장 (S3에 업로드)
        df = pd.DataFrame(excel_data)
        excel_buffer = df.to_excel(index=False, engine='openpyxl')

        # S3에 업로드
        s3_client.put_object(Bucket=S3_BUCKET, Key='aws_resources_status.xlsx', Body=excel_buffer)

        return {
            'statusCode': 200,
            'body': json.dumps('AWS 리소스 상태가 업데이트되었습니다.')
        }

    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        send_sns_message(error_message)
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps(f'오류 발생: {str(e)}')
        }

def get_ec2_instances():
    """특정 태그와 보안 그룹 조건에 맞는 EC2 인스턴스를 필터링"""
    response = ec2_client.describe_instances()
    matching_instances = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            # Name 태그 값 가져오기
            name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), None)
            # Usage 태그 값 가져오기
            usage_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Usage'), None)
            # Usage 태그가 'prod-name'인지 확인
            if usage_tag == 'prod-name':
                # 특정 보안 그룹 ID가 없는지 확인
                if not any(sg['GroupId'] == EC2_SG_ID for sg in instance.get('SecurityGroups', [])):
                    # HostName 태그 값 가져오기
                    host_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'HostName'), 'N/A')

                    # 조건에 맞는 인스턴스를 리스트에 추가
                    matching_instances.append({
                        'Name': name_tag,
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'HostName': host_name
                    })
    return matching_instances

def get_all_albs():
    """모든 ALB 정보를 반환"""
    response = elbv2_client.describe_load_balancers()
    return response['LoadBalancers']

def get_alb_ips(alb_info):
    """특정 ALB의 IP 주소를 반환"""
    ip_addresses = set()
    for zone in alb_info['AvailabilityZones']:
        for address in zone['LoadBalancerAddresses']:
            ip = address.get('IpAddress')
            if ip:
                ip_addresses.add(ip)
    return ip_addresses

def get_network_interface_info():
    """EC2 네트워크 인터페이스에서 Public IP, Public DNS, Security Group 정보 가져오기"""
    response = ec2_client.describe_network_interfaces()
    network_info = []
    for interface in response['NetworkInterfaces']:
        association = interface.get('Association', {})
        if association and 'PublicIp' in association:
            # Security Group 정보 추출
            security_groups = [group['GroupId'] for group in interface['Groups']]
            security_group_ids = ', '.join(security_groups) if security_groups else 'N/A'

            # 네트워크 정보 추가
            network_info.append({
                'Name': 'EC2 Network Interface',
                'Type': 'N/A',
                'Public IP': association.get('PublicIp', 'N/A'),
                'Public DNS': association.get('PublicDnsName', 'N/A'),
                'Security Group ID': security_group_ids
            })
    return network_info

def get_rds_public_ips():
    """RDS 인스턴스에서 Public IP, DB Name, DB Endpoint 가져오기"""
    response = rds_client.describe_db_instances()
    rds_info = []
    for db_instance in response['DBInstances']:
        if db_instance.get('PubliclyAccessible', False):
            rds_info.append({
                'Name': db_instance['DBInstanceIdentifier'],
                'Type': 'RDS Instance',
                'Public IP': db_instance['Endpoint']['Address'],
                'Public DNS': db_instance['Endpoint']['Address'],
                'Security Group ID': ', '.join([sg['VpcSecurityGroupId'] for sg in db_instance['VpcSecurityGroups']])
            })
    return rds_info

def get_cloudfront_info():
    """CloudFront 배포 정보 가져오기 (Public DNS)"""
    response = cloudfront_client.list_distributions()
    cloudfront_info = []
    for distribution in response['DistributionList'].get('Items', []):
        cloudfront_info.append({
            'Name': distribution['Id'],
            'Type': 'CloudFront Distribution',
            'Public IP': 'N/A',
            'Public DNS': distribution['DomainName'],
            'Security Group ID': 'N/A'  # CloudFront는 Security Group이 없음
        })
    return cloudfront_info
