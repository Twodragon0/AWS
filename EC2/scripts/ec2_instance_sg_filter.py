import boto3
import pandas as pd

# EC2 클라이언트 생성
ec2 = boto3.client('ec2', region_name='ap-northeast-2')

# 인스턴스 정보 가져오기 (페이징 처리 포함)
instances = []
paginator = ec2.get_paginator('describe_instances')
for page in paginator.paginate():
    for reservation in page['Reservations']:
        for instance in reservation['Instances']:
            instances.append(instance)

# 결과를 저장할 리스트
matching_instances = []

# 특정 보안 그룹 ID를 제외하기 위해 변수로 설정
excluded_sg_id = 'sg-xx'  # 실제 제외하려는 보안 그룹 ID로 변경하세요

# 인스턴스 순회
for instance in instances:
    # 보안 그룹에 excluded_sg_id가 없는지 확인
    security_groups = instance.get('SecurityGroups', [])
    if any(sg['GroupId'] == excluded_sg_id for sg in security_groups):
        continue  # 제외된 보안 그룹이 있으면 다음 인스턴스로 이동

    # Name 태그 값 가져오기
    name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), None)
    
    if name_tag and 'default' in name_tag:
        # HostName 태그 값 가져오기 (선택 사항)
        host_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'HostName'), 'N/A')
        
        # 조건에 맞는 인스턴스를 리스트에 추가
        matching_instances.append({
            'Name': name_tag,  # Name 태그 값 추가
            'InstanceId': instance['InstanceId'],
            'InstanceType': instance['InstanceType'],
            'State': instance['State']['Name'],
            'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
            'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
            'HostName': host_name  # HostName 태그 값 추가
        })

# 필터링된 인스턴스가 있는지 확인
if matching_instances:
    # 데이터프레임으로 변환
    df = pd.DataFrame(matching_instances)
    
    # 엑셀 파일로 저장
    df.to_excel('matching_instances.xlsx', index=False)
    
    print("Matching instances have been saved to 'matching_instances.xlsx'.")
else:
    print("No instances matched the criteria.")
