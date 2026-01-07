"""
로깅 유틸리티 모듈
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str = 'isms',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 콘솔만 출력)
        format_string: 로그 포맷 문자열
    
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 포맷 설정
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택적)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

