"""
EC2 인스턴스 정보 수집 스크립트
ISMS-P 인증을 위한 EC2 인스턴스 목록 생성

출력 형식: CSV
"""

import sys
from pathlib import Path
from typing import List, Any
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from utils.aws_clients import get_aws_clients
from utils.config import Config
from utils.logger import setup_logger
from utils.exceptions import AssetCollectionError
from utils.exporters import DataExporter
from botocore.exceptions import ClientError

# 로거 설정
logger = setup_logger('isms.ec2_info')


def collect_ec2_instances(config: Config) -> tuple[List[List[Any]], List[str]]:
    """
    EC2 인스턴스 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        (데이터 리스트, 헤더 리스트) 튜플
    """
    logger.info("EC2 인스턴스 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    ec2_client = clients.get_client('ec2')
    ec2_data = []
    
    headers = [
        'HostName', 'Instance ID', 'Spec', 'OS', 'Version',
        'Availability Zone', 'Public IP', 'Private IP', 'Usage', 'Status'
    ]
    
    try:
        response = ec2_client.describe_instances()
        
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                # 태그에서 정보 추출
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                host_name = tags.get('Name', None)
                usage = tags.get('Usage', None)
                
                # 인스턴스 정보 추출
                instance_id = instance.get('InstanceId', 'N/A')
                spec = instance.get('InstanceType', 'N/A')
                os = instance.get('Platform', 'Linux/UNIX')
                version = instance.get('ImageId', 'N/A')
                availability_zone = instance.get('Placement', {}).get('AvailabilityZone', 'N/A')
                public_ip = instance.get('PublicIpAddress', 'N/A')
                private_ip = instance.get('PrivateIpAddress', 'N/A')
                status = instance.get('State', {}).get('Name', 'N/A')
                
                ec2_data.append([
                    host_name, instance_id, spec, os, version,
                    availability_zone, public_ip, private_ip, usage, status
                ])
        
        logger.info(f"EC2 인스턴스 {len(ec2_data)}개 수집 완료")
        return ec2_data, headers
    
    except ClientError as e:
        logger.error(f"EC2 인스턴스 수집 실패: {e}")
        raise AssetCollectionError(f"EC2 인스턴스 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # EC2 인스턴스 정보 수집
        data, headers = collect_ec2_instances(config)
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"ec2_info_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"EC2 인스턴스 정보를 '{output_file}' 파일로 내보냈습니다.")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
