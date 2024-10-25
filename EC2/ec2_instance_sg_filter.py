import boto3
import pandas as pd

# EC2 클라이언트 생성
ec2 = boto3.client('ec2', region_name='ap-northeast-2')

# 인스턴스 정보 가져오기
response = ec2.describe_instances()

# 결과를 저장할 리스트
matching_instances = []

# 인스턴스 순회
for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        # Name 태그 값 가져오기
        name_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), None)
        # Usage 태그 값 가져오기
        usage_tag = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Usage'), None)
        # 모든 태그에서 값이 특정 이름 확인
        if any(tag['Value'] == 'prod-name' for tag in instance.get('Tags', [])):
            # 보안 그룹에 특정 S/G가 없는지 확인
            if not any(sg['GroupId'] == 'sg-xxx' for sg in instance.get('SecurityGroups', [])):
                # HostName 태그 값 가져오기
                host_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'HostName'), 'N/A')
                
                # 조건에 맞는 인스턴스를 리스트에 추가
                matching_instances.append({
                    'Name': name_tag,  # Name 태그 값 추가
                    'InstanceId': instance['InstanceId'],
                    'InstanceType': instance['InstanceType'],
                    'State': instance['State']['Name'],
                    'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                })

# 필터링된 인스턴스가 있는지 확인
if matching_instances:
    # 데이터프레임으로 변환
    df = pd.DataFrame(matching_instances)

    # 엑셀 파일로 저장
    df.to_excel('ec2_instance_sg_filter.xlsx', index=False)

    print("Matching instances have been saved to 'ec2_instance_sg_filter.xlsx'.")
else:
    print("No instances matched the criteria.")
