"""
ISMS-P 2025 가이드 기반 Prowler & Trivy 통합 보안 스캔 스크립트

개선 사항:
- 타입 힌팅 추가
- 에러 처리 강화
- 로깅 시스템 통합
- 설정 관리 개선
- ISMS-P 2025 가이드 반영
"""

import sys
import subprocess
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config
from utils.logger import setup_logger
from utils.exceptions import AssetCollectionError

# 로거 설정
logger = setup_logger('isms.prowler_trivy_scan')


def run_prowler(
    output_format: str = 'html',
    output_dir: Optional[str] = None,
    compliance_framework: Optional[str] = None,
    aws_profile: Optional[str] = None,
    aws_region: Optional[str] = None
) -> Path:
    """
    Prowler AWS 보안 점검 실행
    
    Args:
        output_format: 출력 형식 (html, json, csv)
        output_dir: 출력 디렉토리
        compliance_framework: 컴플라이언스 프레임워크 (cis, nist 등)
        aws_profile: AWS 프로필 이름 (기본값: twodragon)
        aws_region: AWS 리전 (기본값: ap-northeast-2)
    
    Returns:
        생성된 보고서 파일 경로
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) if output_dir else Path('.')
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_file = output_path / f"prowler_report_{timestamp}.{output_format}"
    
    # Prowler 명령어 구성
    cmd = ['prowler', 'aws', '-M', output_format, '-f', str(report_file)]
    
    # AWS profile 지정 (기본값: twodragon)
    profile = aws_profile or os.getenv('AWS_PROFILE', 'twodragon')
    if profile:
        cmd.extend(['--profile', profile])
        logger.info(f"AWS Profile 사용: {profile}")
    
    # AWS 리전 지정
    region = aws_region or os.getenv('AWS_REGION', 'ap-northeast-2')
    if region:
        cmd.extend(['--region', region])
    
    if compliance_framework:
        cmd.extend(['-c', compliance_framework])
    
    # ISMS-P 2025 관련 추가 옵션
    cmd.extend(['--verbose'])
    
    try:
        logger.info("Prowler AWS 보안 점검 실행 중...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1시간 타임아웃
            env={**os.environ, 'AWS_PROFILE': profile} if profile else os.environ
        )
        
        if result.returncode == 0:
            logger.info(f"Prowler 보고서 생성 완료: {report_file}")
            return report_file
        else:
            logger.error(f"Prowler 실행 실패: {result.stderr}")
            raise AssetCollectionError(f"Prowler 실행 실패: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        logger.error("Prowler 실행 타임아웃")
        raise AssetCollectionError("Prowler 실행이 시간 초과되었습니다")
    except FileNotFoundError:
        logger.error("Prowler가 설치되지 않았습니다. 'pip install prowler' 실행 필요")
        raise AssetCollectionError("Prowler가 설치되지 않았습니다")
    except subprocess.CalledProcessError as e:
        logger.error(f"Prowler 실행 중 오류 발생: {e}")
        raise AssetCollectionError(f"Prowler 실행 실패: {e}")


def run_trivy_ecr(
    repository: str,
    image_tag: str,
    account_id: str,
    region: str,
    output_dir: Optional[str] = None
) -> Path:
    """
    Trivy로 AWS ECR 이미지 보안 점검 실행
    
    Args:
        repository: ECR 리포지토리 이름
        image_tag: 이미지 태그
        account_id: AWS 계정 ID
        region: AWS 리전
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 보고서 파일 경로
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) if output_dir else Path('.')
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_file = output_path / f"trivy_ecr_report_{timestamp}.json"
    image_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{repository}:{image_tag}"
    
    try:
        # ECR 로그인
        logger.info(f"ECR 로그인 중: {region}")
        ecr_login_cmd = [
            'aws', 'ecr', 'get-login-password', '--region', region
        ]
        login_result = subprocess.run(
            ecr_login_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        docker_login_cmd = [
            'docker', 'login', '--username', 'AWS',
            '--password-stdin',
            f"{account_id}.dkr.ecr.{region}.amazonaws.com"
        ]
        subprocess.run(
            docker_login_cmd,
            input=login_result.stdout,
            text=True,
            check=True
        )
        
        # 이미지 Pull
        logger.info(f"Docker 이미지 Pull 중: {image_uri}")
        subprocess.run(
            ['docker', 'pull', image_uri],
            check=True,
            timeout=600  # 10분 타임아웃
        )
        
        # Trivy 스캔
        logger.info(f"Trivy 이미지 스캔 실행 중: {image_uri}")
        trivy_cmd = [
            'trivy', 'image',
            '--format', 'json',
            '--output', str(report_file),
            image_uri
        ]
        subprocess.run(trivy_cmd, check=True, timeout=1800)  # 30분 타임아웃
        
        logger.info(f"Trivy ECR 보고서 생성 완료: {report_file}")
        return report_file
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Trivy ECR 스캔 실패: {e}")
        raise AssetCollectionError(f"Trivy ECR 스캔 실패: {e}")
    except FileNotFoundError:
        logger.error("Trivy 또는 Docker가 설치되지 않았습니다")
        raise AssetCollectionError("Trivy 또는 Docker가 설치되지 않았습니다")


def run_trivy_github(
    repo_url: str,
    branch: str = "main",
    output_dir: Optional[str] = None
) -> Path:
    """
    Trivy로 GitHub 리포지토리의 Dockerfile 및 IaC 점검
    
    Args:
        repo_url: GitHub 리포지토리 URL
        branch: 브랜치 이름
        output_dir: 출력 디렉토리
    
    Returns:
        생성된 보고서 파일 경로
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) if output_dir else Path('.')
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_file = output_path / f"trivy_github_report_{timestamp}.json"
    repo_dir = repo_url.split('/')[-1].replace(".git", "")
    
    try:
        # 리포지토리 클론
        logger.info(f"GitHub 리포지토리 클론 중: {repo_url} (branch: {branch})")
        subprocess.run(
            ['git', 'clone', '-b', branch, repo_url],
            check=True,
            timeout=300  # 5분 타임아웃
        )
        
        # Trivy 스캔
        logger.info(f"Trivy IaC 스캔 실행 중: {repo_dir}")
        trivy_cmd = [
            'trivy', 'config',
            '--format', 'json',
            '--output', str(report_file),
            repo_dir
        ]
        subprocess.run(trivy_cmd, check=True, timeout=1800)  # 30분 타임아웃
        
        logger.info(f"Trivy GitHub 보고서 생성 완료: {report_file}")
        return report_file
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Trivy GitHub 스캔 실패: {e}")
        raise AssetCollectionError(f"Trivy GitHub 스캔 실패: {e}")
    except FileNotFoundError:
        logger.error("Trivy 또는 Git이 설치되지 않았습니다")
        raise AssetCollectionError("Trivy 또는 Git이 설치되지 않았습니다")


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        output_dir = config.output_dir
        
        logger.info("=== ISMS-P 2025 보안 스캔 시작 ===")
        logger.info(f"AWS Profile: {config.aws_profile}")
        logger.info(f"AWS Region: {config.aws_region}")
        
        # Prowler 실행 (AWS 보안 점검)
        logger.info("1. Prowler AWS 보안 점검 실행")
        prowler_report = run_prowler(
            output_format='json',
            output_dir=output_dir,
            compliance_framework='cis',  # CIS 기준 점검
            aws_profile=config.aws_profile,
            aws_region=config.aws_region
        )
        logger.info(f"Prowler 보고서: {prowler_report}")
        
        # ECR 이미지 스캔 (예제 - 실제 사용 시 파라미터 수정 필요)
        # logger.info("2. Trivy ECR 이미지 스캔 실행")
        # trivy_ecr_report = run_trivy_ecr(
        #     repository="my-repo",
        #     image_tag="latest",
        #     account_id="123456789012",
        #     region="ap-northeast-2",
        #     output_dir=output_dir
        # )
        
        logger.info("=== ISMS-P 2025 보안 스캔 완료 ===")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
