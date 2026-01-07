"""
S3 버킷 상세 보안 정보 수집 스크립트
ISMS-P 인증을 위한 S3 버킷 보안 설정 점검

출력 형식: CSV

이 스크립트는 다음 보안 설정을 점검합니다:
- 버킷 암호화
- 버킷 로깅
- ACL 설정
- 버킷 정책
- 퍼블릭 액세스 차단
- 암호화 규칙
"""

import sys
import json
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
logger = setup_logger('isms.s3_script')


def get_bucket_acl(client, bucket: str) -> str:
    """
    버킷 ACL 정보 조회
    
    Args:
        client: S3 클라이언트
        bucket: 버킷 이름
    
    Returns:
        ACL 정보 문자열
    """
    try:
        response = client.get_bucket_acl(Bucket=bucket)
        output = "-"
        for grant in response.get("Grants", []):
            try:
                grantee = grant.get("Grantee", {})
                if "URI" in grantee and "AllUsers" in grantee["URI"]:
                    output = grant.get("Permission", "-")
                    break
            except (KeyError, TypeError):
                continue
        return output
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'AccessDenied':
            return "Access Denied"
        return "-"


def get_bucket_encryption(client, bucket: str) -> str:
    """
    버킷 암호화 정보 조회
    
    Args:
        client: S3 클라이언트
        bucket: 버킷 이름
    
    Returns:
        "Good" (암호화 설정됨) 또는 "Weak" (암호화 미설정)
    """
    try:
        client.get_bucket_encryption(Bucket=bucket)
        return "Good"
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
            return "Weak"
        return "Error"


def get_bucket_logging(client, bucket: str) -> str:
    """
    버킷 로깅 설정 정보 조회
    
    Args:
        client: S3 클라이언트
        bucket: 버킷 이름
    
    Returns:
        "Good" (로깅 설정됨) 또는 "Weak" (로깅 미설정)
    """
    try:
        response = client.get_bucket_logging(Bucket=bucket)
        if response.get('LoggingEnabled'):
            return "Good"
        return "Weak"
    except ClientError as e:
        return "Weak"


def get_bucket_policy(client, bucket: str) -> str:
    """
    버킷 정책 조회
    
    Args:
        client: S3 클라이언트
        bucket: 버킷 이름
    
    Returns:
        정책 JSON 문자열 또는 "-"
    """
    try:
        response = client.get_bucket_policy(Bucket=bucket)
        policy_str = response.get("Policy", "{}")
        # JSON 문자열을 파싱하여 포맷팅
        policy_json = json.loads(policy_str)
        return json.dumps(policy_json, indent=2).replace('"', "'")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchBucketPolicy':
            return "-"
        return f"Error: {error_code}"


def get_public_access_block(client, bucket: str) -> str:
    """
    버킷 퍼블릭 액세스 차단 설정 조회
    
    Args:
        client: S3 클라이언트
        bucket: 버킷 이름
    
    Returns:
        "True" (모든 차단 활성화), "False" (일부 비활성화), 또는 "Unknown"
    """
    try:
        response = client.get_public_access_block(Bucket=bucket)
        check = response.get("PublicAccessBlockConfiguration", {})
        
        block_public_acls = check.get("BlockPublicAcls", False)
        ignore_public_acls = check.get("IgnorePublicAcls", False)
        block_public_policy = check.get("BlockPublicPolicy", False)
        restrict_public_buckets = check.get("RestrictPublicBuckets", False)
        
        # 모든 설정이 활성화되어 있는지 확인
        if all([block_public_acls, ignore_public_acls, block_public_policy, restrict_public_buckets]):
            return "True"
        elif any([block_public_acls, ignore_public_acls, block_public_policy, restrict_public_buckets]):
            return "Partial"
        else:
            return "False"
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchPublicAccessBlockConfiguration':
            return "Not configured"
        return "Unknown"


def get_bucket_encryption_rules(client, bucket: str) -> str:
    """
    버킷 암호화 규칙 조회
    
    Args:
        client: S3 클라이언트
        bucket: 버킷 이름
    
    Returns:
        암호화 규칙 JSON 문자열 또는 "-"
    """
    try:
        response = client.get_bucket_encryption(Bucket=bucket)
        rules = response.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
        return json.dumps(rules, indent=2) if rules else "-"
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
            return "-"
        return f"Error: {error_code}"


def collect_s3_security_info(config: Config) -> tuple[List[List[Any]], List[str]]:
    """
    S3 버킷 보안 정보 수집
    
    Args:
        config: 설정 객체
    
    Returns:
        (데이터 리스트, 헤더 리스트) 튜플
    """
    logger.info("S3 버킷 보안 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
    
    if not clients.test_connection():
        raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    s3_client = clients.get_client('s3')
    s3_data = []
    
    headers = [
        'Name', 'Bucket Encryption', 'Bucket Logging', 'ACL',
        'Bucket Policy', 'Public Access Block', 'Encryption Rules'
    ]
    
    try:
        response = s3_client.list_buckets()
        
        for bucket in response.get("Buckets", []):
            bucket_name = bucket["Name"]
            
            logger.debug(f"버킷 정보 수집 중: {bucket_name}")
            
            bucket_encryption = get_bucket_encryption(s3_client, bucket_name)
            bucket_logging = get_bucket_logging(s3_client, bucket_name)
            bucket_acl = get_bucket_acl(s3_client, bucket_name)
            bucket_policy = get_bucket_policy(s3_client, bucket_name)
            public_access_block = get_public_access_block(s3_client, bucket_name)
            encryption_rules = get_bucket_encryption_rules(s3_client, bucket_name)
            
            s3_data.append([
                bucket_name, bucket_encryption, bucket_logging,
                bucket_acl, bucket_policy, public_access_block, encryption_rules
            ])
        
        logger.info(f"S3 버킷 보안 정보 {len(s3_data)}개 수집 완료")
        return s3_data, headers
    
    except ClientError as e:
        logger.error(f"S3 버킷 보안 정보 수집 실패: {e}")
        raise AssetCollectionError(f"S3 버킷 보안 정보 수집 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # S3 버킷 보안 정보 수집
        data, headers = collect_s3_security_info(config)
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"s3_bucket_info_{timestamp}.csv"
        
        # CSV 파일로 내보내기
        DataExporter.export_to_csv(data, headers, str(output_file))
        
        logger.info(f"S3 버킷 보안 정보를 '{output_file}' 파일로 내보냈습니다.")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
