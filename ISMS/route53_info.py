"""
Route 53 호스티드 존 및 레코드 정보 수집 스크립트
ISMS-P 인증을 위한 Route 53 레코드 목록 생성

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
logger = setup_logger('isms.route53_info')


def collect_route53_records(config: Config) -> List[Dict[str, Any]]:
    """
    Route 53 호스티드 존 및 레코드 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        Route 53 레코드 정보 딕셔너리 리스트
    """
    logger.info("Route 53 레코드 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    route53_client = clients.get_client('route53')
    route53_data = []
    
    try:
        # 호스티드 존 목록
        hosted_zones = route53_client.list_hosted_zones()
        
        for zone in hosted_zones.get('HostedZones', []):
            zone_id = zone['Id'].split('/')[-1]
            zone_name = zone['Name']
            
            # 레코드 세트 조회
            paginator = route53_client.get_paginator('list_resource_record_sets')
            
            for page in paginator.paginate(HostedZoneId=zone_id):
                for record in page.get('ResourceRecordSets', []):
                    record_values = [r.get('Value', '') for r in record.get('ResourceRecords', [])]
                    alias_target = record.get('AliasTarget', {})
                    
                    route53_data.append({
                        'HostedZoneId': zone_id,
                        'HostedZoneName': zone_name,
                        'Name': record.get('Name', 'N/A'),
                        'Type': record.get('Type', 'N/A'),
                        'TTL': record.get('TTL', 'N/A'),
                        'RoutingPolicy': record.get('SetIdentifier', 'N/A'),  # 라우팅 정책 식별자
                        'Values': ', '.join(record_values) if record_values else 'N/A',
                        'AliasDNSName': alias_target.get('DNSName', 'N/A'),
                        'AliasHostedZoneId': alias_target.get('HostedZoneId', 'N/A')
                    })
        
        logger.info(f"Route 53 레코드 {len(route53_data)}개 수집 완료")
        return route53_data
    
    except ClientError as e:
        logger.error(f"Route 53 레코드 수집 실패: {e}")
        raise AssetCollectionError(f"Route 53 레코드 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # Route 53 레코드 정보 수집
        records = collect_route53_records(config)
        
        # 딕셔너리 리스트를 행 리스트로 변환
        if records:
            headers = list(records[0].keys())
            data = [[record.get(h, 'N/A') for h in headers] for record in records]
        else:
            headers = [
                'HostedZoneId', 'HostedZoneName', 'Name', 'Type',
                'TTL', 'RoutingPolicy', 'Values', 'AliasDNSName', 'AliasHostedZoneId'
            ]
            data = []
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"route53_records_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"Route 53 레코드를 '{output_file}' 파일로 내보냈습니다.")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
