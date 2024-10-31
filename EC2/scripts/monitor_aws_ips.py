import boto3
import requests
import json
import time
import pandas as pd
import os

# AWS SDK 클라이언트
client = boto3.client('elbv2')
ec2_client = boto3.client('ec2')
rds_client = boto3.client('rds')
cloudfront_client = boto3.client('cloudfront')

# 슬랙 웹훅 URL (Slack에서 생성한 Webhook URL을 입력하세요)
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/your/slack/webhook'

# 이전에 저장된 IP 주소
previous_ips = {}

# 엑셀 파일 경로
EXCEL_FILE_PATH = 'aws_public_ip_addresses_with_security_groups.xlsx'

def get_all_albs():
    """ 모든 ALB 정보를 반환 """
    response = client.describe_load_balancers()
    return response['LoadBalancers']

def get_alb_ips(alb_info):
    """ 특정 ALB의 IP 주소를 반환 """
    ip_addresses = set()
    for zone in alb_info['AvailabilityZones']:
        for address in zone['LoadBalancerAddresses']:
            ip_addresses.add(address['IpAddress'])
    return ip_addresses

def get_network_interface_info():
    """ EC2 네트워크 인터페이스에서 Public IP, Public DNS, Security Group 정보 가져오기 """
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
    """ RDS 인스턴스에서 Public IP, DB Name, DB Endpoint 가져오기 """
    response = rds_client.describe_db_instances()
    rds_info = []
    for db_instance in response['DBInstances']:
        if db_instance.get('PubliclyAccessible', False):
            rds_info.append({
                'Name': 'RDS Instance',
                'Type': 'N/A',
                'Public IP': db_instance['Endpoint']['Address'],
                'Public DNS': db_instance['Endpoint']['Address'],
                'Security Group ID': ', '.join([sg['VpcSecurityGroupId'] for sg in db_instance['VpcSecurityGroups']])
            })
    return rds_info

def get_cloudfront_info():
    """ CloudFront 배포 정보 가져오기 (Public DNS) """
    response = cloudfront_client.list_distributions()
    cloudfront_info = []
    for distribution in response['DistributionList'].get('Items', []):
        cloudfront_info.append({
            'Name': 'CloudFront Distribution',
            'Type': 'N/A',
            'Public IP': 'N/A',
            'Public DNS': distribution['DomainName'],
            'Security Group ID': 'N/A'  # CloudFront는 Security Group이 없음
        })
    return cloudfront_info

def save_to_excel(data):
    """ ALB, EC2, RDS 및 CloudFront 정보를 엑셀 파일에 저장 """
    df = pd.DataFrame(data)
    df.to_excel(EXCEL_FILE_PATH, index=False)

def send_slack_message(message):
    """ 슬랙으로 메시지 전송 """
    slack_data = {'text': message}
    response = requests.post(
        SLACK_WEBHOOK_URL, 
        data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(f'Slack message failed with status code {response.status_code}, response: {response.text}')

def monitor_aws_public_ips():
    """ 모든 AWS 리소스의 IP 주소 변경 모니터링 """
    global previous_ips
    
    while True:
        try:
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
            
            # ALB 정보 추가
            for alb in albs:
                alb_name = alb['LoadBalancerName']
                alb_scheme = alb['Scheme']  # ALB의 타입 (internet-facing 또는 internal)
                current_ips = get_alb_ips(alb)

                # ALB 타입에 따라 Public 또는 Private IP로 구분
                alb_type = "Public" if alb_scheme == "internet-facing" else "Private"
                
                # 엑셀 저장을 위한 데이터 구성
                for ip in current_ips:
                    excel_data.append({
                        'Name': alb_name,
                        'Type': alb_type,
                        'Public IP': ip,
                        'Public DNS': 'N/A',  # ALB는 Public DNS를 따로 제공하지 않음
                        'Security Group ID': 'N/A'  # ALB는 Security Group ID가 따로 존재하지 않음
                    })
                
                # 이전 IP 주소와 비교하여 변경 여부 확인
                if alb_name in previous_ips and current_ips != previous_ips[alb_name]:
                    message = f"Resource '{alb_name}'의 IP 주소가 변경되었습니다! ({alb_type})\n이전 IP: {previous_ips[alb_name]}\n새로운 IP: {current_ips}"
                    send_slack_message(message)
                    print(message)
                
                # 이전 IP 주소를 현재 IP 주소로 업데이트
                previous_ips[alb_name] = current_ips

            # EC2 네트워크 인터페이스 정보 추가
            for network_interface in network_interfaces:
                excel_data.append(network_interface)

            # RDS 인스턴스 정보 추가
            for rds_instance in rds_instances:
                excel_data.append(rds_instance)

            # CloudFront 배포 정보 추가
            for cloudfront in cloudfront_distributions:
                excel_data.append(cloudfront)

            # 모든 데이터를 엑셀 파일에 저장
            save_to_excel(excel_data)
            print(f"엑셀 파일에 AWS Public IP 정보가 저장되었습니다: {EXCEL_FILE_PATH}")
        
        except Exception as e:
            print(f"오류 발생: {str(e)}")
        
        # 60초마다 IP 변경 여부 확인
        time.sleep(60)

if __name__ == '__main__':
    # 첫 번째 실행 시 엑셀에 저장
    albs = get_all_albs()
    network_interfaces = get_network_interface_info()
    rds_instances = get_rds_public_ips()
    cloudfront_distributions = get_cloudfront_info()
    
    excel_data = []

    # ALB 정보 추가
    for alb in albs:
        alb_name = alb['LoadBalancerName']
        alb_scheme = alb['Scheme']
        current_ips = get_alb_ips(alb)
        alb_type = "Public" if alb_scheme == "internet-facing" else "Private"
        
        for ip in current_ips:
            excel_data.append({
                'Name': alb_name,
                'Type': alb_type,
                'Public IP': ip,
                'Public DNS': 'N/A',
                'Security Group ID': 'N/A'
            })
    
    # EC2 네트워크 인터페이스 정보 추가
    for network_interface in network_interfaces:
        excel_data.append(network_interface)

    # RDS 인스턴스 정보 추가
    for rds_instance in rds_instances:
        excel_data.append(rds_instance)

    # CloudFront 배포 정보 추가
    for cloudfront in cloudfront_distributions:
        excel_data.append(cloudfront)
    
    # 초기 데이터를 엑셀에 저장
    save_to_excel(excel_data)
    print(f"초기 AWS Public IP 정보가 엑셀 파일로 저장되었습니다: {EXCEL_FILE_PATH}")
    
    # 이후 모니터링 시작
    monitor_aws_public_ips()
