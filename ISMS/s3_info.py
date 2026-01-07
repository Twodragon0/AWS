"""
S3 버킷 정보 수집 스크립트
ISMS-P 인증을 위한 S3 버킷 목록 생성

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
logger = setup_logger('isms.s3_info')


def collect_s3_buckets(config: Config) -> tuple[List[List[Any]], List[str]]:
    """
    S3 버킷 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        (데이터 리스트, 헤더 리스트) 튜플
    """
    logger.info("S3 버킷 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    s3_client = clients.get_client('s3')
    s3_data = []
    
    headers = ['BucketName', 'Access', 'Location', 'Purpose']
    
    try:
        response = s3_client.list_buckets()
        
        for bucket in response.get('Buckets', []):
            bucket_name = bucket['Name']
            
            # 버킷 정책 상태 조회
            try:
                bucket_policy_status_resp = s3_client.get_bucket_policy_status(Bucket=bucket_name)
                is_public = bucket_policy_status_resp.get('PolicyStatus', {}).get('IsPublic', False)
                access = 'Public' if is_public else 'Bucket and objects not public'
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'NoSuchBucketPolicy':
                    # ACL 확인
                    try:
                        acl_resp = s3_client.get_bucket_acl(Bucket=bucket_name)
                        is_public_acl = False
                        for grant in acl_resp.get('Grants', []):
                            grantee = grant.get('Grantee', {})
                            if 'URI' in grantee:
                                uri = grantee['URI']
                                if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                                    is_public_acl = True
                                    break
                        access = 'Objects can be public' if is_public_acl else 'Bucket and objects not public'
                    except ClientError:
                        access = 'Bucket and objects not public'
                else:
                    logger.warning(f"버킷 정책 상태 조회 실패 ({bucket_name}): {e}")
                    access = 'Unknown'
            
            # 버킷 위치 조회
            try:
                location_resp = s3_client.get_bucket_location(Bucket=bucket_name)
                location = location_resp.get('LocationConstraint', 'us-east-1')
                if not location:  # us-east-1은 None으로 반환됨
                    location = 'us-east-1'
            except ClientError as e:
                logger.warning(f"버킷 위치 조회 실패 ({bucket_name}): {e}")
                location = 'Unknown'
            
            # 용도는 기본값 (실제 사용 시 태그나 다른 방법으로 수집 가능)
            purpose = 'General'
            
            s3_data.append([bucket_name, access, location, purpose])
        
        logger.info(f"S3 버킷 {len(s3_data)}개 수집 완료")
        return s3_data, headers
    
    except ClientError as e:
        logger.error(f"S3 버킷 수집 실패: {e}")
        raise AssetCollectionError(f"S3 버킷 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # S3 버킷 정보 수집
        data, headers = collect_s3_buckets(config)
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"s3_buckets_info_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"S3 버킷 정보를 '{output_file}' 파일로 내보냈습니다.")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
