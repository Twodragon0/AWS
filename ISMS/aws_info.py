"""
AWS 자산 정보 수집 스크립트
ISMS-P 인증을 위한 AWS 자산 목록 생성

이 스크립트는 다음 AWS 서비스의 자산 정보를 수집합니다:
- EC2 인스턴스
- S3 버킷
- ECR 리포지토리
- IAM 역할 및 정책
- Route 53 호스티드 존 및 레코드
- RDS 인스턴스
- CloudFront 배포
- Lambda 함수

출력 형식: Excel (XLSX)
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from utils.aws_clients import get_aws_clients
from utils.config import Config
from utils.logger import setup_logger
from utils.exceptions import AssetCollectionError, ExportError
from utils.exporters import DataExporter
from botocore.exceptions import ClientError
import pandas as pd

# 로거 설정
logger = setup_logger('isms.aws_info')


class AWSAssetCollector:
    """AWS 자산 수집 클래스"""
    
    def __init__(self, config: Config):
        """
        초기화
        
        Args:
            config: 설정 객체
        """
        self.config = config
        self.clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
        
        # AWS 연결 테스트
        if not self.clients.test_connection():
            raise AssetCollectionError("AWS 연결 실패. 자격 증명을 확인하세요.")
    
    def collect_ec2_instances(self) -> List[List[Any]]:
        """
        EC2 인스턴스 정보 수집
        
        Returns:
            EC2 인스턴스 정보 리스트
        """
        logger.info("EC2 인스턴스 정보 수집 중...")
        ec2_client = self.clients.get_client('ec2')
ec2_data = []

        try:
            response = ec2_client.describe_instances()
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    # 태그에서 정보 추출
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    host_name = tags.get('Name', 'N/A')
                    usage = tags.get('Usage', 'N/A')
                    
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
            return ec2_data
        
        except ClientError as e:
            logger.error(f"EC2 인스턴스 수집 실패: {e}")
            raise AssetCollectionError(f"EC2 인스턴스 수집 실패: {e}")
    
    def collect_s3_buckets(self) -> List[List[Any]]:
        """
        S3 버킷 정보 수집
        
        Returns:
            S3 버킷 정보 리스트
        """
        logger.info("S3 버킷 정보 수집 중...")
        s3_client = self.clients.get_client('s3')
        s3_data = []
        
        try:
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                # 버킷 상세 정보 수집
                acl_info = self._get_bucket_acl(s3_client, bucket_name)
                encryption_info = self._get_bucket_encryption(s3_client, bucket_name)
                logging_info = self._get_bucket_logging(s3_client, bucket_name)
                policy_info = self._get_bucket_policy(s3_client, bucket_name)
                public_access_info = self._get_public_access_block(s3_client, bucket_name)
                
                s3_data.append([
                    bucket_name, acl_info, encryption_info,
                    logging_info, policy_info, public_access_info
                ])
            
            logger.info(f"S3 버킷 {len(s3_data)}개 수집 완료")
            return s3_data
        
        except ClientError as e:
            logger.error(f"S3 버킷 수집 실패: {e}")
            raise AssetCollectionError(f"S3 버킷 수집 실패: {e}")
    
    def _get_bucket_acl(self, client, bucket: str) -> str:
    """버킷 ACL 정보 조회"""
    try:
        response = client.get_bucket_acl(Bucket=bucket)
        acl_info = []
            for grant in response.get('Grants', []):
                grantee = grant.get('Grantee', {})
                permission = grant.get('Permission', '')
                grantee_type = grantee.get('Type', 'Unknown')
                acl_info.append(f"{grantee_type}: {permission}")
            return ', '.join(acl_info) if acl_info else 'N/A'
    except ClientError as e:
            return f"Error: {e.response.get('Error', {}).get('Code', 'Unknown')}"

    def _get_bucket_encryption(self, client, bucket: str) -> str:
    """버킷 암호화 정보 조회"""
    try:
        response = client.get_bucket_encryption(Bucket=bucket)
            encryption_rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            return json.dumps(encryption_rules, indent=2) if encryption_rules else 'N/A'
    except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                return 'Not configured'
            return f"Error: {error_code}"

    def _get_bucket_logging(self, client, bucket: str) -> str:
    """버킷 로깅 설정 정보 조회"""
    try:
        response = client.get_bucket_logging(Bucket=bucket)
        logging_info = response.get('LoggingEnabled', {})
        if logging_info:
            return f"TargetBucket: {logging_info.get('TargetBucket')}, TargetPrefix: {logging_info.get('TargetPrefix')}"
            return "Not enabled"
    except ClientError as e:
            return f"Error: {e.response.get('Error', {}).get('Code', 'Unknown')}"

    def _get_bucket_policy(self, client, bucket: str) -> str:
    """버킷 정책 조회"""
    try:
        response = client.get_bucket_policy(Bucket=bucket)
            policy = json.loads(response.get('Policy', '{}'))
            return json.dumps(policy, indent=2)
    except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchBucketPolicy':
                return 'No policy'
            return f"Error: {error_code}"

    def _get_public_access_block(self, client, bucket: str) -> str:
    """버킷 퍼블릭 액세스 차단 정보 조회"""
    try:
        response = client.get_public_access_block(Bucket=bucket)
            block_config = response.get('PublicAccessBlockConfiguration', {})
        return json.dumps(block_config, indent=2)
    except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchPublicAccessBlockConfiguration':
                return 'Not configured'
            return f"Error: {error_code}"
    
    def collect_ecr_repositories(self) -> List[List[Any]]:
        """
        ECR 리포지토리 정보 수집
        
        Returns:
            ECR 리포지토리 정보 리스트
        """
        logger.info("ECR 리포지토리 정보 수집 중...")
        ecr_client = self.clients.get_client('ecr', region=self.config.aws_region)
    ecr_data = []
        
        try:
            paginator = ecr_client.get_paginator('describe_repositories')
            
            for page in paginator.paginate():
                for repo in page.get('repositories', []):
                    repository_name = repo.get('repositoryName', 'N/A')
                    repository_uri = repo.get('repositoryUri', 'N/A')
                    created_at = repo.get('createdAt', datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
                    image_scanning = repo.get('imageScanningConfiguration', {}).get('scanOnPush', False)
                    image_tag_mutability = repo.get('imageTagMutability', 'MUTABLE')
        
        ecr_data.append([
                        repository_name, repository_uri, created_at,
                        image_scanning, image_tag_mutability, 'N/A'  # lifecycle_policy는 별도 조회 필요
                    ])
            
            logger.info(f"ECR 리포지토리 {len(ecr_data)}개 수집 완료")
    return ecr_data

        except ClientError as e:
            logger.error(f"ECR 리포지토리 수집 실패: {e}")
            raise AssetCollectionError(f"ECR 리포지토리 수집 실패: {e}")
    
    def collect_iam_roles(self) -> List[List[Any]]:
        """
        IAM 역할 및 정책 정보 수집
        
        Returns:
            IAM 역할 및 정책 정보 리스트
        """
        logger.info("IAM 역할 및 정책 정보 수집 중...")
        iam_client = self.clients.get_client('iam')
        iam_data = []
        
        try:
            # 모든 역할 목록 가져오기
            paginator = iam_client.get_paginator('list_roles')
            
        for page in paginator.paginate():
                for role in page.get('Roles', []):
                    role_name = role.get('RoleName', 'N/A')
                    
                    # 인라인 정책
                    try:
                        inline_paginator = iam_client.get_paginator('list_role_policies')
                        for inline_page in inline_paginator.paginate(RoleName=role_name):
                            for policy_name in inline_page.get('PolicyNames', []):
                                try:
                                    policy_response = iam_client.get_role_policy(
                                        RoleName=role_name,
                                        PolicyName=policy_name
                                    )
                                    policy_doc = policy_response.get('PolicyDocument', {})
                                    iam_data.append([
                                        role_name, policy_name, 'inline',
                                        json.dumps(policy_doc, indent=2)
                                    ])
                                except ClientError as e:
                                    logger.warning(f"IAM 인라인 정책 조회 실패 ({role_name}/{policy_name}): {e}")
                    except ClientError as e:
                        logger.warning(f"IAM 인라인 정책 목록 조회 실패 ({role_name}): {e}")
                    
                    # 관리형 정책
                    try:
                        managed_paginator = iam_client.get_paginator('list_attached_role_policies')
                        for managed_page in managed_paginator.paginate(RoleName=role_name):
                            for policy in managed_page.get('AttachedPolicies', []):
                                policy_arn = policy.get('PolicyArn', '')
                                policy_name = policy.get('PolicyName', 'N/A')
                                
                                try:
                                    policy_response = iam_client.get_policy(PolicyArn=policy_arn)
                                    default_version_id = policy_response['Policy']['DefaultVersionId']
                                    version_response = iam_client.get_policy_version(
                                        PolicyArn=policy_arn,
                                        VersionId=default_version_id
                                    )
                                    policy_doc = version_response['PolicyVersion'].get('Document', {})
                                    iam_data.append([
                                        role_name, policy_name, 'managed',
                                        json.dumps(policy_doc, indent=2)
                                    ])
                                except ClientError as e:
                                    logger.warning(f"IAM 관리형 정책 조회 실패 ({policy_arn}): {e}")
                    except ClientError as e:
                        logger.warning(f"IAM 관리형 정책 목록 조회 실패 ({role_name}): {e}")
            
            logger.info(f"IAM 역할 및 정책 {len(iam_data)}개 수집 완료")
            return iam_data
        
        except ClientError as e:
            logger.error(f"IAM 역할 수집 실패: {e}")
            raise AssetCollectionError(f"IAM 역할 수집 실패: {e}")
    
    def collect_route53_records(self) -> List[Dict[str, Any]]:
        """
        Route 53 호스티드 존 및 레코드 정보 수집
        
        Returns:
            Route 53 레코드 정보 딕셔너리 리스트
        """
        logger.info("Route 53 레코드 정보 수집 중...")
        route53_client = self.clients.get_client('route53')
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
                'Values': ', '.join(record_values) if record_values else 'N/A',
                'AliasDNSName': alias_target.get('DNSName', 'N/A'),
                'AliasHostedZoneId': alias_target.get('HostedZoneId', 'N/A')
                        })
            
            logger.info(f"Route 53 레코드 {len(route53_data)}개 수집 완료")
    return route53_data

        except ClientError as e:
            logger.error(f"Route 53 레코드 수집 실패: {e}")
            raise AssetCollectionError(f"Route 53 레코드 수집 실패: {e}")
    
    def collect_rds_instances(self) -> List[Dict[str, Any]]:
        """
        RDS 인스턴스 정보 수집
        
        Returns:
            RDS 인스턴스 정보 딕셔너리 리스트
        """
        logger.info("RDS 인스턴스 정보 수집 중...")
        rds_client = self.clients.get_client('rds')
        rds_data = []
        
        try:
            instances = rds_client.describe_db_instances()
            
            for instance in instances.get('DBInstances', []):
                endpoint = instance.get('Endpoint', {})
                rds_data.append({
                    'DBInstanceIdentifier': instance.get('DBInstanceIdentifier', 'N/A'),
                    'DBInstanceClass': instance.get('DBInstanceClass', 'N/A'),
                    'Engine': instance.get('Engine', 'N/A'),
                    'EngineVersion': instance.get('EngineVersion', 'N/A'),
                    'AvailabilityZone': instance.get('AvailabilityZone', 'N/A'),
                    'DBInstanceStatus': instance.get('DBInstanceStatus', 'N/A'),
                    'Endpoint': endpoint.get('Address', 'N/A')
                })
            
            logger.info(f"RDS 인스턴스 {len(rds_data)}개 수집 완료")
            return rds_data
        
        except ClientError as e:
            logger.error(f"RDS 인스턴스 수집 실패: {e}")
            raise AssetCollectionError(f"RDS 인스턴스 수집 실패: {e}")
    
    def collect_cloudfront_distributions(self) -> List[Dict[str, Any]]:
        """
        CloudFront 배포 정보 수집
        
        Returns:
            CloudFront 배포 정보 딕셔너리 리스트
        """
        logger.info("CloudFront 배포 정보 수집 중...")
        cloudfront_client = self.clients.get_client('cloudfront')
        cloudfront_data = []
        
        try:
            response = cloudfront_client.list_distributions()
            distributions = response.get('DistributionList', {}).get('Items', [])
            
    for dist in distributions:
                origins = dist.get('Origins', {}).get('Items', [])
                origin_domain = origins[0].get('DomainName', 'N/A') if origins else 'N/A'
                
                cloudfront_data.append({
                    'Id': dist.get('Id', 'N/A'),
                    'DomainName': dist.get('DomainName', 'N/A'),
                    'Status': dist.get('Status', 'N/A'),
                    'Enabled': dist.get('Enabled', False),
                    'OriginDomainName': origin_domain,
                    'Comment': dist.get('Comment', 'N/A')
                })
            
            logger.info(f"CloudFront 배포 {len(cloudfront_data)}개 수집 완료")
            return cloudfront_data
        
        except ClientError as e:
            logger.error(f"CloudFront 배포 수집 실패: {e}")
            raise AssetCollectionError(f"CloudFront 배포 수집 실패: {e}")
    
    def collect_lambda_functions(self) -> List[Dict[str, Any]]:
        """
        Lambda 함수 정보 수집
        
        Returns:
            Lambda 함수 정보 딕셔너리 리스트
        """
        logger.info("Lambda 함수 정보 수집 중...")
        lambda_client = self.clients.get_client('lambda')
        lambda_data = []
        
        try:
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for func in page.get('Functions', []):
                    lambda_data.append({
                        'FunctionName': func.get('FunctionName', 'N/A'),
                        'Runtime': func.get('Runtime', 'N/A'),
                        'Handler': func.get('Handler', 'N/A'),
                        'Timeout': func.get('Timeout', 0),
                        'MemorySize': func.get('MemorySize', 0),
                        'LastModified': func.get('LastModified', 'N/A').strftime("%Y-%m-%d %H:%M:%S") if func.get('LastModified') else 'N/A'
                    })
            
            logger.info(f"Lambda 함수 {len(lambda_data)}개 수집 완료")
            return lambda_data
        
        except ClientError as e:
            logger.error(f"Lambda 함수 수집 실패: {e}")
            raise AssetCollectionError(f"Lambda 함수 수집 실패: {e}")
    
    def export_to_excel(self, output_path: str) -> None:
        """
        수집한 모든 자산 정보를 Excel 파일로 내보내기
        
        Args:
            output_path: 출력 파일 경로
        """
        logger.info("자산 정보 수집 시작...")
        
        try:
            # 자산 정보 수집
            ec2_data = self.collect_ec2_instances()
            s3_data = self.collect_s3_buckets()
            ecr_data = self.collect_ecr_repositories()
            iam_data = self.collect_iam_roles()
            route53_data = self.collect_route53_records()
            rds_data = self.collect_rds_instances()
            cloudfront_data = self.collect_cloudfront_distributions()
            lambda_data = self.collect_lambda_functions()
            
            # DataFrame 생성
            dataframes = {
                'EC2 Instances': pd.DataFrame(
                    ec2_data,
                    columns=['HostName', 'Instance ID', 'Spec', 'OS', 'Version',
                            'Availability Zone', 'Public IP', 'Private IP', 'Usage', 'Status']
                ),
                'S3 Buckets': pd.DataFrame(
                    s3_data,
                    columns=['BucketName', 'ACL', 'Encryption', 'Logging', 'Policy', 'Public Access Block']
                ),
                'ECR Repositories': pd.DataFrame(
                    ecr_data,
                    columns=['Repository Name', 'Repository URI', 'Created At',
                            'Image Scanning', 'Tag Mutability', 'Lifecycle Policy']
                ),
                'IAM Roles': pd.DataFrame(
                    iam_data,
                    columns=['Role Name', 'Policy Name', 'Policy Type', 'Policy Document']
                ),
                'Route53 Records': pd.DataFrame(route53_data),
                'RDS Instances': pd.DataFrame(rds_data),
                'CloudFront Distributions': pd.DataFrame(cloudfront_data),
                'Lambda Functions': pd.DataFrame(lambda_data)
            }
            
            # Excel 파일로 내보내기
            DataExporter.export_to_excel(dataframes, output_path)
            logger.info(f"모든 AWS 자산 정보를 '{output_path}' 파일로 내보냈습니다.")
        
        except Exception as e:
            logger.error(f"자산 정보 내보내기 실패: {e}")
            raise ExportError(f"자산 정보 내보내기 실패: {e}")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # 자산 수집기 생성
        collector = AWSAssetCollector(config)
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(config.output_dir) / f"aws_assets_isms_p_{timestamp}.xlsx"
        
        # 자산 정보 수집 및 내보내기
        collector.export_to_excel(str(output_file))
        
        logger.info("작업 완료!")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
