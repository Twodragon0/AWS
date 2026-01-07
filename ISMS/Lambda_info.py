"""
Lambda 함수 정보 수집 스크립트
ISMS-P 인증을 위한 Lambda 함수 목록 생성

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
logger = setup_logger('isms.lambda_info')


def collect_lambda_functions(config: Config) -> tuple[List[List[Any]], List[str]]:
    """
    Lambda 함수 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        (데이터 리스트, 헤더 리스트) 튜플
    """
    logger.info("Lambda 함수 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    lambda_client = clients.get_client('lambda')
    lambda_data = []
    
    headers = [
        'Function Name', 'Runtime', 'Last Modified',
        'Memory Size', 'Timeout', 'VPC Configured'
    ]
    
    try:
        paginator = lambda_client.get_paginator('list_functions')
        
        for page in paginator.paginate():
            for function in page.get('Functions', []):
                function_name = function.get('FunctionName', 'N/A')
                runtime = function.get('Runtime', 'N/A')
                last_modified = function.get('LastModified', None)
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S") if last_modified else 'N/A'
                memory_size = function.get('MemorySize', 0)
                timeout = function.get('Timeout', 0)
                
                # VPC 설정 확인
                vpc_config = function.get('VpcConfig', {})
                vpc_configured = 'Yes' if vpc_config.get('VpcId') else 'No'
                
                lambda_data.append([
                    function_name, runtime, last_modified_str,
                    memory_size, timeout, vpc_configured
                ])
        
        logger.info(f"Lambda 함수 {len(lambda_data)}개 수집 완료")
        return lambda_data, headers
    
    except ClientError as e:
        logger.error(f"Lambda 함수 수집 실패: {e}")
        raise AssetCollectionError(f"Lambda 함수 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # Lambda 함수 정보 수집
        data, headers = collect_lambda_functions(config)
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"aws_lambda_inventory_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"Lambda 함수 정보를 '{output_file}' 파일로 내보냈습니다.")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
