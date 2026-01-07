"""
EC2 인스턴스 네트워크 인터페이스 정보 수집 스크립트
ISMS-P 인증을 위한 EC2 ENI 목록 생성

출력 형식: CSV
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
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
logger = setup_logger('isms.ec2_eni')


def collect_ec2_network_interfaces(config: Config) -> List[Dict[str, Any]]:
    """
    EC2 인스턴스 네트워크 인터페이스 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        EC2 네트워크 인터페이스 정보 딕셔너리 리스트
    """
    logger.info("EC2 네트워크 인터페이스 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    ec2_client = clients.get_client('ec2')
    instance_details = []
    
    try:
        response = ec2_client.describe_instances()
        
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance.get('InstanceId', 'N/A')
                
                # 태그에서 이름 추출
                name = 'N/A'
                for tag in instance.get('Tags', []):
                    if tag.get('Key') == 'Name':
                        name = tag.get('Value', 'N/A')
                        break
                
                private_ip_address = instance.get('PrivateIpAddress', '')
                public_ip_address = instance.get('PublicIpAddress', '')
                
                # 네트워크 인터페이스 정보
                network_interfaces = instance.get('NetworkInterfaces', [])
                
                if network_interfaces:
                    for network_interface in network_interfaces:
                        network_interface_id = network_interface.get('NetworkInterfaceId', '')
                        instance_details.append({
                            'Name': name,
                            'Instance ID': instance_id,
                            'Private IP': private_ip_address,
                            'Public IP': public_ip_address,
                            'Network Interface ID': network_interface_id
                        })
                else:
                    # 네트워크 인터페이스가 없는 경우에도 기본 정보 기록
                    instance_details.append({
                        'Name': name,
                        'Instance ID': instance_id,
                        'Private IP': private_ip_address,
                        'Public IP': public_ip_address,
                        'Network Interface ID': 'N/A'
                    })
        
        logger.info(f"EC2 네트워크 인터페이스 {len(instance_details)}개 수집 완료")
        return instance_details
    
    except ClientError as e:
        logger.error(f"EC2 네트워크 인터페이스 수집 실패: {e}")
        raise AssetCollectionError(f"EC2 네트워크 인터페이스 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # EC2 네트워크 인터페이스 정보 수집
        records = collect_ec2_network_interfaces(config)
        
        # 딕셔너리 리스트를 행 리스트로 변환
        if records:
            headers = list(records[0].keys())
            data = [[record.get(h, 'N/A') for h in headers] for record in records]
        else:
            headers = ['Name', 'Instance ID', 'Private IP', 'Public IP', 'Network Interface ID']
            data = []
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"instance_details_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"EC2 네트워크 인터페이스 정보를 '{output_file}' 파일로 내보냈습니다.")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
