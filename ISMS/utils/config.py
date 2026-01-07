"""
설정 관리 모듈
환경 변수 및 기본 설정 관리
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """ISMS-P 스크립트 설정"""
    # AWS 설정
    aws_region: str = os.getenv('AWS_REGION', 'ap-northeast-2')
    aws_profile: Optional[str] = os.getenv('AWS_PROFILE', None)
    
    # 출력 설정
    output_dir: str = os.getenv('ISMS_OUTPUT_DIR', '.')
    output_format: str = os.getenv('ISMS_OUTPUT_FORMAT', 'csv')  # csv, xlsx, json
    
    # 로깅 설정
    log_level: str = os.getenv('ISMS_LOG_LEVEL', 'INFO')
    log_file: Optional[str] = os.getenv('ISMS_LOG_FILE', None)
    
    # Google Drive 설정 (선택적)
    google_service_account_file: Optional[str] = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', None)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """환경 변수에서 설정 로드"""
        return cls()

