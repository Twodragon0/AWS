"""
EC2 및 S3 자산 정보를 Google Drive에 업로드하는 스크립트
ISMS-P 인증을 위한 자산 목록을 Google Drive에 자동 업로드

주의: 이 스크립트는 Google Drive API 인증이 필요합니다.
GOOGLE_SERVICE_ACCOUNT_FILE 환경 변수에 서비스 계정 JSON 파일 경로를 설정하세요.
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
from utils.exceptions import AssetCollectionError, ExportError
from utils.exporters import DataExporter
from botocore.exceptions import ClientError

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from openpyxl.utils.dataframe import dataframe_to_rows
    import pandas as pd
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

# 로거 설정
logger = setup_logger('isms.ec2_s3_drive')


def collect_ec2_instances(config: Config) -> tuple[List[List[Any]], List[str]]:
    """EC2 인스턴스 정보 수집"""
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
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                host_name = tags.get('Name', None)
                usage = tags.get('Usage', None)
                
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


def collect_s3_buckets(config: Config) -> tuple[List[List[Any]], List[str]]:
    """S3 버킷 정보 수집"""
    logger.info("S3 버킷 정보 수집 중...")
    
    clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
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
                    access = 'Bucket and objects not public'
                else:
                    logger.warning(f"버킷 정책 상태 조회 실패 ({bucket_name}): {e}")
                    access = 'Unknown'
            
            # 버킷 위치 조회
            try:
                location_resp = s3_client.get_bucket_location(Bucket=bucket_name)
                location = location_resp.get('LocationConstraint', 'us-east-1')
                if not location:
                    location = 'us-east-1'
            except ClientError as e:
                logger.warning(f"버킷 위치 조회 실패 ({bucket_name}): {e}")
                location = 'Unknown'
            
            purpose = 'General'
            s3_data.append([bucket_name, access, location, purpose])
        
        logger.info(f"S3 버킷 {len(s3_data)}개 수집 완료")
        return s3_data, headers
    
    except ClientError as e:
        logger.error(f"S3 버킷 수집 실패: {e}")
        raise AssetCollectionError(f"S3 버킷 수집 실패: {e}")


def upload_to_google_drive(config: Config, ec2_data: List[List[Any]], ec2_headers: List[str],
                           s3_data: List[List[Any]], s3_headers: List[str]) -> None:
    """
    Google Drive에 데이터 업로드
    
    Args:
        config: 설정 객체
        ec2_data: EC2 데이터
        ec2_headers: EC2 헤더
        s3_data: S3 데이터
        s3_headers: S3 헤더
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        raise ImportError(
            "Google Drive 관련 모듈이 필요합니다. "
            "다음 명령어로 설치하세요: pip install gspread oauth2client"
        )
    
    if not config.google_service_account_file:
        raise ExportError(
            "Google 서비스 계정 파일이 설정되지 않았습니다. "
            "GOOGLE_SERVICE_ACCOUNT_FILE 환경 변수를 설정하세요."
        )
    
    logger.info("Google Drive에 업로드 중...")
    
    try:
        # Google Drive 인증
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        service_account_file = Path(config.google_service_account_file)
        if not service_account_file.exists():
            raise ExportError(f"서비스 계정 파일을 찾을 수 없습니다: {service_account_file}")
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            str(service_account_file), scope
        )
        client = gspread.authorize(creds)
        
        # 스프레드시트 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        spreadsheet_name = f'AWS Assets ISMS-P {timestamp}'
        sh = client.create(spreadsheet_name)
        
        # EC2 시트 생성 및 데이터 추가
        worksheet_ec2 = sh.add_worksheet(title='EC2 Instances', rows="100", cols="20")
        ec2_df = pd.DataFrame(ec2_data, columns=ec2_headers)
        for r_idx, row in enumerate(dataframe_to_rows(ec2_df, index=False, header=True)):
            worksheet_ec2.insert_row(row, r_idx + 1)
        
        # S3 시트 생성 및 데이터 추가
        worksheet_s3 = sh.add_worksheet(title='S3 Buckets', rows="100", cols="20")
        s3_df = pd.DataFrame(s3_data, columns=s3_headers)
        for r_idx, row in enumerate(dataframe_to_rows(s3_df, index=False, header=True)):
            worksheet_s3.insert_row(row, r_idx + 1)
        
        logger.info(f"Google Drive에 업로드 완료: {spreadsheet_name}")
        logger.info(f"스프레드시트 URL: {sh.url}")
    
    except Exception as e:
        logger.error(f"Google Drive 업로드 실패: {e}")
        raise ExportError(f"Google Drive 업로드 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # EC2 및 S3 정보 수집
        ec2_data, ec2_headers = collect_ec2_instances(config)
        s3_data, s3_headers = collect_s3_buckets(config)
        
        # 로컬 Excel 파일로도 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"aws_assets_isms_p_{timestamp}.xlsx"
        
        dataframes = {
            'EC2 Instances': pd.DataFrame(ec2_data, columns=ec2_headers),
            'S3 Buckets': pd.DataFrame(s3_data, columns=s3_headers)
        }
        DataExporter.export_to_excel(dataframes, str(output_file))
        logger.info(f"로컬 Excel 파일 생성 완료: {output_file}")
        
        # Google Drive에 업로드 (선택적)
        if config.google_service_account_file:
            upload_to_google_drive(config, ec2_data, ec2_headers, s3_data, s3_headers)
        else:
            logger.info("Google Drive 업로드를 건너뜁니다. (GOOGLE_SERVICE_ACCOUNT_FILE 환경 변수 미설정)")
    
    except ImportError as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
