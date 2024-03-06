import boto3
import csv

# Boto3 EC2 클라이언트 생성
ec2_client = boto3.client('ec2')

# EC2 인스턴스 정보 조회
response = ec2_client.describe_instances()

# CSV 파일 생성 및 헤더 작성
with open('ec2_info.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['HostName', 'Instance ID', 'Spec', 'OS', 'Version', 'Availability Zone', 'Public IP', 'Private IP', 'Usage', 'Status'])

    # 인스턴스 정보를 CSV 파일에 작성
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            # 태그에서 호스트 이름과 용도 찾기
            host_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), None)
            usage = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Usage'), None)

            # 필요한 정보 추출
            instance_id = instance['InstanceId']
            spec = instance['InstanceType']
            os = instance.get('Platform', 'Linux/UNIX')  # 'Platform' 키가 없는 경우 Linux/UNIX로 가정
            version = instance.get('ImageId', 'N/A')
            availability_zone = instance['Placement']['AvailabilityZone']
            public_ip = instance.get('PublicIpAddress', 'N/A')
            private_ip = instance['PrivateIpAddress']
            status = instance['State']['Name']

            # CSV 파일에 한 줄 작성
            writer.writerow([host_name, instance_id, spec, os, version, availability_zone, public_ip, private_ip, usage, status])
