"""
AWS 클라이언트 관리 모듈
중앙화된 AWS 클라이언트 생성 및 관리
"""

import boto3
from typing import Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)


class AWSClientManager:
    """AWS 클라이언트 관리자"""
    
    def __init__(self, region: str = 'ap-northeast-2', profile: Optional[str] = None):
        """
        AWS 클라이언트 관리자 초기화
        
        Args:
            region: AWS 리전
            profile: AWS 프로필 이름 (선택적)
        """
        self.region = region
        self.profile = profile
        self._session = None
        self._clients: Dict[str, any] = {}
    
    @property
    def session(self):
        """Boto3 세션 가져오기 (지연 로딩)"""
        if self._session is None:
            if self.profile:
                self._session = boto3.Session(profile_name=self.profile, region_name=self.region)
            else:
                self._session = boto3.Session(region_name=self.region)
        return self._session
    
    def get_client(self, service_name: str, region: Optional[str] = None):
        """
        AWS 서비스 클라이언트 가져오기 (캐싱)
        
        Args:
            service_name: AWS 서비스 이름 (예: 'ec2', 's3')
            region: 리전 (None이면 기본 리전 사용)
        
        Returns:
            Boto3 클라이언트 인스턴스
        """
        cache_key = f"{service_name}:{region or self.region}"
        
        if cache_key not in self._clients:
            try:
                if region:
                    self._clients[cache_key] = self.session.client(service_name, region_name=region)
                else:
                    self._clients[cache_key] = self.session.client(service_name)
                logger.debug(f"AWS 클라이언트 생성: {cache_key}")
            except (ClientError, BotoCoreError) as e:
                logger.error(f"AWS 클라이언트 생성 실패 ({service_name}): {e}")
                raise
        
        return self._clients[cache_key]
    
    def test_connection(self) -> bool:
        """
        AWS 연결 테스트
        
        Returns:
            연결 성공 여부
        """
        try:
            sts = self.get_client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"AWS 연결 성공: Account={identity.get('Account')}, User={identity.get('Arn')}")
            return True
        except Exception as e:
            logger.error(f"AWS 연결 실패: {e}")
            return False


# 전역 클라이언트 관리자 인스턴스
_client_manager: Optional[AWSClientManager] = None


def get_aws_clients(region: str = 'ap-northeast-2', profile: Optional[str] = None) -> AWSClientManager:
    """
    AWS 클라이언트 관리자 가져오기 (싱글톤)
    
    Args:
        region: AWS 리전
        profile: AWS 프로필 이름
    
    Returns:
        AWSClientManager 인스턴스
    """
    global _client_manager
    
    if _client_manager is None:
        _client_manager = AWSClientManager(region=region, profile=profile)
    
    return _client_manager

