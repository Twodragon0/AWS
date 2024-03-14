import boto3
import csv

# boto3 클라이언트 초기화
lambda_client = boto3.client('lambda')

# 모든 Lambda 함수 목록 가져오기
response = lambda_client.list_functions()

# CSV 파일 준비
with open('aws_lambda_inventory.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    # 헤더 행 작성
    writer.writerow(['Function Name', 'Runtime', 'Last Modified', 'Memory Size', 'Timeout', 'VPC Configured'])

    # 각 Lambda 함수에 대해 반복
    for function in response['Functions']:
        # Lambda 함수가 VPC에 구성되어 있는지 확인
        vpc_configured = 'Yes' if function.get('VpcConfig', {}).get('VpcId') else 'No'
        # 각 Lambda 함수의 세부 정보를 CSV에 작성
        writer.writerow([
            function['FunctionName'],
            function['Runtime'],
            function['LastModified'],
            function['MemorySize'],
            function['Timeout'],
            vpc_configured
        ])
