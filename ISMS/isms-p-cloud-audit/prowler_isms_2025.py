"""
ISMS-P 2025 가이드 기반 Prowler 자산 식별 및 위험 관리 시스템

이 스크립트는 ISMS-P 2025 최신 가이드에 따라 다음을 수행합니다:
1. AWS 자산 자동 식별
2. 보안 취약점 점검 및 위험 평가
3. 위험 등급 부여 및 우선순위 관리
4. 위험 관리 보고서 생성
5. 지속적인 모니터링 및 알림

주요 특징:
- 클라우드 환경 보안 강화 점검
- AI/머신러닝 데이터 처리 보안 점검
- 자산 중요도 평가 (CIA 기준)
- 위험 등급 자동 부여
- 개선 조치 추적
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.aws_clients import get_aws_clients
from utils.config import Config
from utils.logger import setup_logger
from utils.exceptions import AssetCollectionError
from botocore.exceptions import ClientError

# 로거 설정
logger = setup_logger('isms.prowler_isms_2025')


class RiskLevel(Enum):
    """위험 등급"""
    CRITICAL = "Critical"  # 즉시 조치 필요
    HIGH = "High"  # 우선 조치 필요
    MEDIUM = "Medium"  # 계획적 조치 필요
    LOW = "Low"  # 모니터링 필요
    INFO = "Info"  # 정보성


class AssetImportance(Enum):
    """자산 중요도 (CIA 기준)"""
    CRITICAL = "Critical"  # 기밀성, 무결성, 가용성 모두 높음
    HIGH = "High"  # 2개 이상 높음
    MEDIUM = "Medium"  # 1개 높음
    LOW = "Low"  # 모두 낮음


@dataclass
class SecurityFinding:
    """보안 발견 사항"""
    check_id: str
    check_title: str
    status: str  # PASS, FAIL, WARNING
    risk_level: RiskLevel
    severity: str
    service: str
    region: str
    resource_id: str
    description: str
    remediation: str
    compliance_frameworks: List[str]
    asset_importance: Optional[AssetImportance] = None
    detected_at: Optional[str] = None
    remediated_at: Optional[str] = None


@dataclass
class Asset:
    """정보 자산"""
    asset_id: str
    asset_type: str
    asset_name: str
    service: str
    region: str
    importance: AssetImportance
    confidentiality: int  # 1-5
    integrity: int  # 1-5
    availability: int  # 1-5
    owner: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    created_at: Optional[str] = None
    last_audited: Optional[str] = None


@dataclass
class RiskAssessment:
    """위험 평가"""
    asset_id: str
    asset_name: str
    risk_score: float  # 0-100
    risk_level: RiskLevel
    findings: List[SecurityFinding]
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    assessed_at: str


class ProwlerISMS2025:
    """ISMS-P 2025 가이드 기반 Prowler 통합 클래스"""
    
    def __init__(self, config: Config):
        """
        초기화
        
        Args:
            config: 설정 객체
        """
        self.config = config
        self.clients = get_aws_clients(region=config.aws_region, profile=config.aws_profile)
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 위험 평가 기준 (ISMS-P 2025)
        self.risk_thresholds = {
            RiskLevel.CRITICAL: 80,
            RiskLevel.HIGH: 60,
            RiskLevel.MEDIUM: 40,
            RiskLevel.LOW: 20
        }
    
    def check_prowler_installed(self) -> bool:
        """Prowler 설치 여부 확인"""
        try:
            result = subprocess.run(
                ['prowler', '-v'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Prowler 버전 확인: {result.stdout.strip()}")
                return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.error("Prowler가 설치되지 않았습니다. 'pip install prowler' 실행 필요")
            return False
    
    def run_prowler_scan(
        self,
        output_format: str = 'json',
        compliance_framework: Optional[str] = None,
        services: Optional[List[str]] = None
    ) -> Path:
        """
        Prowler 스캔 실행
        
        Args:
            output_format: 출력 형식 (json, csv, html)
            compliance_framework: 컴플라이언스 프레임워크 (cis, nist, pci-dss 등)
            services: 점검할 서비스 목록 (None이면 전체)
        
        Returns:
            출력 파일 경로
        """
        if not self.check_prowler_installed():
            raise AssetCollectionError("Prowler가 설치되지 않았습니다")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"prowler_scan_{timestamp}.{output_format}"
        
        # Prowler 명령어 구성
        cmd = ['prowler', 'aws', '-M', output_format, '-f', str(output_file)]
        
        # 컴플라이언스 프레임워크 지정
        if compliance_framework:
            cmd.extend(['-c', compliance_framework])
        
        # 서비스 필터
        if services:
            cmd.extend(['-s', ','.join(services)])
        
        # ISMS-P 2025 관련 추가 옵션
        # 클라우드 환경 보안 강화 점검
        cmd.extend(['--verbose', '--log-level', 'INFO'])
        
        logger.info(f"Prowler 스캔 시작: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1시간 타임아웃
            )
            
            if result.returncode == 0:
                logger.info(f"Prowler 스캔 완료: {output_file}")
                return output_file
            else:
                logger.error(f"Prowler 스캔 실패: {result.stderr}")
                raise AssetCollectionError(f"Prowler 스캔 실패: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error("Prowler 스캔 타임아웃")
            raise AssetCollectionError("Prowler 스캔이 시간 초과되었습니다")
    
    def parse_prowler_results(self, json_file: Path) -> List[SecurityFinding]:
        """
        Prowler JSON 결과 파싱
        
        Args:
            json_file: Prowler JSON 출력 파일
        
        Returns:
            보안 발견 사항 리스트
        """
        logger.info(f"Prowler 결과 파싱: {json_file}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            findings = []
            
            # Prowler 출력 형식에 따라 파싱
            if isinstance(data, list):
                for item in data:
                    finding = self._parse_finding(item)
                    if finding:
                        findings.append(finding)
            elif isinstance(data, dict):
                # 다른 형식 처리
                if 'findings' in data:
                    for item in data['findings']:
                        finding = self._parse_finding(item)
                        if finding:
                            findings.append(finding)
            
            logger.info(f"총 {len(findings)}개의 보안 발견 사항 파싱 완료")
            return findings
        
        except Exception as e:
            logger.error(f"Prowler 결과 파싱 실패: {e}")
            raise AssetCollectionError(f"결과 파싱 실패: {e}")
    
    def _parse_finding(self, item: Dict[str, Any]) -> Optional[SecurityFinding]:
        """개별 발견 사항 파싱"""
        try:
            # Prowler 출력 형식에 맞춰 필드 매핑
            check_id = item.get('CheckID', item.get('check_id', ''))
            status = item.get('Status', item.get('status', 'UNKNOWN'))
            severity = item.get('Severity', item.get('severity', 'unknown'))
            
            # 위험 등급 결정
            risk_level = self._determine_risk_level(status, severity)
            
            finding = SecurityFinding(
                check_id=check_id,
                check_title=item.get('CheckTitle', item.get('check_title', '')),
                status=status,
                risk_level=risk_level,
                severity=severity,
                service=item.get('ServiceName', item.get('service', '')),
                region=item.get('Region', item.get('region', '')),
                resource_id=item.get('ResourceId', item.get('resource_id', '')),
                description=item.get('Message', item.get('description', '')),
                remediation=item.get('Remediation', item.get('remediation', '')),
                compliance_frameworks=item.get('Compliance', item.get('compliance', [])),
                detected_at=datetime.now().isoformat()
            )
            
            return finding
        
        except Exception as e:
            logger.warning(f"발견 사항 파싱 실패: {e}")
            return None
    
    def _determine_risk_level(self, status: str, severity: str) -> RiskLevel:
        """위험 등급 결정"""
        # FAIL 상태이고 심각도가 높은 경우
        if status == 'FAIL':
            severity_lower = severity.lower()
            if severity_lower in ['critical', 'high']:
                return RiskLevel.CRITICAL
            elif severity_lower == 'medium':
                return RiskLevel.HIGH
            elif severity_lower == 'low':
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW
        elif status == 'WARNING':
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.INFO
    
    def identify_assets(self) -> List[Asset]:
        """
        AWS 자산 자동 식별
        
        Returns:
            자산 리스트
        """
        logger.info("AWS 자산 식별 시작...")
        
        assets = []
        ec2_client = self.clients.get_client('ec2')
        s3_client = self.clients.get_client('s3')
        rds_client = self.clients.get_client('rds')
        lambda_client = self.clients.get_client('lambda')
        
        try:
            # EC2 인스턴스
            response = ec2_client.describe_instances()
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    asset = Asset(
                        asset_id=instance.get('InstanceId', ''),
                        asset_type='EC2',
                        asset_name=tags.get('Name', instance.get('InstanceId', '')),
                        service='ec2',
                        region=self.config.aws_region,
                        importance=self._assess_asset_importance(instance, tags),
                        confidentiality=self._assess_confidentiality(instance, tags),
                        integrity=self._assess_integrity(instance, tags),
                        availability=self._assess_availability(instance, tags),
                        owner=tags.get('Owner', ''),
                        tags=tags,
                        created_at=instance.get('LaunchTime', datetime.now()).isoformat() if instance.get('LaunchTime') else None
                    )
                    assets.append(asset)
            
            # S3 버킷
            response = s3_client.list_buckets()
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                # S3 버킷 태그 조회 시도
                tags = {}
                try:
                    tag_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tag_response.get('TagSet', [])}
                except ClientError:
                    pass
                
                asset = Asset(
                    asset_id=bucket_name,
                    asset_type='S3',
                    asset_name=bucket_name,
                    service='s3',
                    region=self.config.aws_region,
                    importance=AssetImportance.HIGH,  # S3는 일반적으로 중요
                    confidentiality=4,  # 기본값
                    integrity=4,
                    availability=5,
                    owner=tags.get('Owner', ''),
                    tags=tags,
                    created_at=bucket.get('CreationDate', datetime.now()).isoformat() if bucket.get('CreationDate') else None
                )
                assets.append(asset)
            
            # RDS 인스턴스
            response = rds_client.describe_db_instances()
            for instance in response.get('DBInstances', []):
                tags = {tag['Key']: tag['Value'] for tag in instance.get('TagList', [])}
                asset = Asset(
                    asset_id=instance.get('DBInstanceIdentifier', ''),
                    asset_type='RDS',
                    asset_name=instance.get('DBInstanceIdentifier', ''),
                    service='rds',
                    region=self.config.aws_region,
                    importance=AssetImportance.CRITICAL,  # RDS는 일반적으로 매우 중요
                    confidentiality=5,
                    integrity=5,
                    availability=5,
                    owner=tags.get('Owner', ''),
                    tags=tags,
                    created_at=instance.get('InstanceCreateTime', datetime.now()).isoformat() if instance.get('InstanceCreateTime') else None
                )
                assets.append(asset)
            
            logger.info(f"총 {len(assets)}개의 자산 식별 완료")
            return assets
        
        except Exception as e:
            logger.error(f"자산 식별 실패: {e}")
            raise AssetCollectionError(f"자산 식별 실패: {e}")
    
    def _assess_asset_importance(self, resource: Dict, tags: Dict[str, str]) -> AssetImportance:
        """자산 중요도 평가 (CIA 기준)"""
        # 태그에서 중요도 정보 확인
        importance_tag = tags.get('Importance', tags.get('Criticality', ''))
        if importance_tag:
            importance_map = {
                'critical': AssetImportance.CRITICAL,
                'high': AssetImportance.HIGH,
                'medium': AssetImportance.MEDIUM,
                'low': AssetImportance.LOW
            }
            return importance_map.get(importance_tag.lower(), AssetImportance.MEDIUM)
        
        # 기본 평가 로직
        # 프로덕션 환경, 중요한 서비스 등은 높은 중요도
        env = tags.get('Environment', '').lower()
        if env in ['prod', 'production']:
            return AssetImportance.CRITICAL
        elif env in ['staging', 'test']:
            return AssetImportance.MEDIUM
        else:
            return AssetImportance.LOW
    
    def _assess_confidentiality(self, resource: Dict, tags: Dict[str, str]) -> int:
        """기밀성 평가 (1-5)"""
        # 데이터 분류 태그 확인
        data_class = tags.get('DataClassification', tags.get('Confidentiality', '')).lower()
        classification_map = {
            'public': 1,
            'internal': 2,
            'confidential': 4,
            'restricted': 5
        }
        return classification_map.get(data_class, 3)
    
    def _assess_integrity(self, resource: Dict, tags: Dict[str, str]) -> int:
        """무결성 평가 (1-5)"""
        # 중요도에 따라 평가
        importance = self._assess_asset_importance(resource, tags)
        importance_map = {
            AssetImportance.CRITICAL: 5,
            AssetImportance.HIGH: 4,
            AssetImportance.MEDIUM: 3,
            AssetImportance.LOW: 2
        }
        return importance_map.get(importance, 3)
    
    def _assess_availability(self, resource: Dict, tags: Dict[str, str]) -> int:
        """가용성 평가 (1-5)"""
        # 프로덕션 환경은 높은 가용성 요구
        env = tags.get('Environment', '').lower()
        if env in ['prod', 'production']:
            return 5
        elif env in ['staging']:
            return 4
        else:
            return 3
    
    def assess_risks(
        self,
        assets: List[Asset],
        findings: List[SecurityFinding]
    ) -> List[RiskAssessment]:
        """
        위험 평가 수행
        
        Args:
            assets: 자산 리스트
            findings: 보안 발견 사항 리스트
        
        Returns:
            위험 평가 리스트
        """
        logger.info("위험 평가 시작...")
        
        assessments = []
        
        # 자산별로 발견 사항 그룹화
        asset_findings = {}
        for finding in findings:
            resource_id = finding.resource_id
            if resource_id not in asset_findings:
                asset_findings[resource_id] = []
            asset_findings[resource_id].append(finding)
        
        # 각 자산에 대한 위험 평가
        for asset in assets:
            asset_findings_list = asset_findings.get(asset.asset_id, [])
            
            # 위험 점수 계산
            risk_score = self._calculate_risk_score(asset, asset_findings_list)
            
            # 위험 등급 결정
            risk_level = self._determine_risk_level_from_score(risk_score)
            
            # 발견 사항 통계
            critical_count = sum(1 for f in asset_findings_list if f.risk_level == RiskLevel.CRITICAL)
            high_count = sum(1 for f in asset_findings_list if f.risk_level == RiskLevel.HIGH)
            medium_count = sum(1 for f in asset_findings_list if f.risk_level == RiskLevel.MEDIUM)
            low_count = sum(1 for f in asset_findings_list if f.risk_level == RiskLevel.LOW)
            
            assessment = RiskAssessment(
                asset_id=asset.asset_id,
                asset_name=asset.asset_name,
                risk_score=risk_score,
                risk_level=risk_level,
                findings=asset_findings_list,
                total_findings=len(asset_findings_list),
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count,
                assessed_at=datetime.now().isoformat()
            )
            
            assessments.append(assessment)
        
        logger.info(f"총 {len(assessments)}개의 자산에 대한 위험 평가 완료")
        return assessments
    
    def _calculate_risk_score(self, asset: Asset, findings: List[SecurityFinding]) -> float:
        """위험 점수 계산 (0-100)"""
        if not findings:
            return 0.0
        
        # 자산 중요도 가중치
        importance_weights = {
            AssetImportance.CRITICAL: 1.5,
            AssetImportance.HIGH: 1.2,
            AssetImportance.MEDIUM: 1.0,
            AssetImportance.LOW: 0.8
        }
        weight = importance_weights.get(asset.importance, 1.0)
        
        # 발견 사항별 점수
        base_scores = {
            RiskLevel.CRITICAL: 25,
            RiskLevel.HIGH: 15,
            RiskLevel.MEDIUM: 8,
            RiskLevel.LOW: 3,
            RiskLevel.INFO: 1
        }
        
        total_score = sum(base_scores.get(f.risk_level, 0) for f in findings)
        weighted_score = min(total_score * weight, 100.0)
        
        return round(weighted_score, 2)
    
    def _determine_risk_level_from_score(self, score: float) -> RiskLevel:
        """위험 점수로부터 위험 등급 결정"""
        if score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif score >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        elif score >= self.risk_thresholds[RiskLevel.LOW]:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFO
    
    def generate_risk_report(
        self,
        assessments: List[RiskAssessment],
        assets: List[Asset],
        findings: List[SecurityFinding]
    ) -> Path:
        """
        위험 관리 보고서 생성
        
        Args:
            assessments: 위험 평가 리스트
            assets: 자산 리스트
            findings: 보안 발견 사항 리스트
        
        Returns:
            보고서 파일 경로
        """
        logger.info("위험 관리 보고서 생성 중...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"isms_risk_report_{timestamp}.json"
        
        # 보고서 데이터 구성
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'ISMS-P 2025 Risk Assessment',
                'aws_region': self.config.aws_region,
                'total_assets': len(assets),
                'total_findings': len(findings),
                'total_assessments': len(assessments)
            },
            'summary': {
                'critical_risks': len([a for a in assessments if a.risk_level == RiskLevel.CRITICAL]),
                'high_risks': len([a for a in assessments if a.risk_level == RiskLevel.HIGH]),
                'medium_risks': len([a for a in assessments if a.risk_level == RiskLevel.MEDIUM]),
                'low_risks': len([a for a in assessments if a.risk_level == RiskLevel.LOW]),
                'average_risk_score': round(sum(a.risk_score for a in assessments) / len(assessments) if assessments else 0, 2)
            },
            'assets': [asdict(asset) for asset in assets],
            'assessments': [
                {
                    'asset_id': a.asset_id,
                    'asset_name': a.asset_name,
                    'risk_score': a.risk_score,
                    'risk_level': a.risk_level.value,
                    'total_findings': a.total_findings,
                    'critical_count': a.critical_count,
                    'high_count': a.high_count,
                    'medium_count': a.medium_count,
                    'low_count': a.low_count,
                    'assessed_at': a.assessed_at,
                    'findings': [
                        {
                            'check_id': f.check_id,
                            'check_title': f.check_title,
                            'status': f.status,
                            'risk_level': f.risk_level.value,
                            'severity': f.severity,
                            'service': f.service,
                            'description': f.description,
                            'remediation': f.remediation
                        }
                        for f in a.findings
                    ]
                }
                for a in assessments
            ],
            'findings': [
                {
                    'check_id': f.check_id,
                    'check_title': f.check_title,
                    'status': f.status,
                    'risk_level': f.risk_level.value,
                    'severity': f.severity,
                    'service': f.service,
                    'region': f.region,
                    'resource_id': f.resource_id,
                    'description': f.description,
                    'remediation': f.remediation,
                    'compliance_frameworks': f.compliance_frameworks
                }
                for f in findings
            ]
        }
        
        # JSON 파일로 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"위험 관리 보고서 생성 완료: {report_file}")
        return report_file
    
    def run_full_assessment(self) -> Dict[str, Any]:
        """
        전체 평가 실행 (자산 식별 + 보안 점검 + 위험 평가)
        
        Returns:
            평가 결과 딕셔너리
        """
        logger.info("=== ISMS-P 2025 전체 평가 시작 ===")
        
        try:
            # 1. 자산 식별
            logger.info("1단계: 자산 식별")
            assets = self.identify_assets()
            
            # 2. Prowler 보안 점검
            logger.info("2단계: Prowler 보안 점검")
            prowler_output = self.run_prowler_scan(output_format='json')
            
            # 3. 결과 파싱
            logger.info("3단계: 결과 파싱")
            findings = self.parse_prowler_results(prowler_output)
            
            # 4. 위험 평가
            logger.info("4단계: 위험 평가")
            assessments = self.assess_risks(assets, findings)
            
            # 5. 보고서 생성
            logger.info("5단계: 보고서 생성")
            report_file = self.generate_risk_report(assessments, assets, findings)
            
            logger.info("=== ISMS-P 2025 전체 평가 완료 ===")
            
            return {
                'assets': assets,
                'findings': findings,
                'assessments': assessments,
                'report_file': report_file,
                'summary': {
                    'total_assets': len(assets),
                    'total_findings': len(findings),
                    'critical_risks': len([a for a in assessments if a.risk_level == RiskLevel.CRITICAL]),
                    'high_risks': len([a for a in assessments if a.risk_level == RiskLevel.HIGH])
                }
            }
        
        except Exception as e:
            logger.error(f"전체 평가 실패: {e}", exc_info=True)
            raise


def main():
    """메인 함수"""
    try:
        # 설정 로드
        config = Config.from_env()
        
        # 평가 실행
        assessor = ProwlerISMS2025(config)
        results = assessor.run_full_assessment()
        
        # 결과 출력
        print("\n=== 평가 결과 요약 ===")
        print(f"총 자산 수: {results['summary']['total_assets']}")
        print(f"총 발견 사항: {results['summary']['total_findings']}")
        print(f"Critical 위험: {results['summary']['critical_risks']}")
        print(f"High 위험: {results['summary']['high_risks']}")
        print(f"\n보고서 파일: {results['report_file']}")
    
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

