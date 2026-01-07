# ISMS-P 2025 가이드 기반 Prowler 자산 식별 및 위험 관리

이 디렉토리는 **ISMS-P 2025 최신 가이드**에 따라 AWS 클라우드 환경의 자산을 자동으로 식별하고, 보안 취약점을 점검하며, 위험을 평가하는 통합 시스템을 제공합니다.

## 개요

ISMS-P 2025 가이드의 주요 요구사항:
- **자산 식별 및 관리**: 클라우드 자산의 자동 식별 및 중요도 평가
- **위험 평가**: CIA(기밀성, 무결성, 가용성) 기준 위험 평가
- **보안 점검**: Prowler를 통한 자동화된 보안 점검
- **지속적인 모니터링**: 정기적인 점검 및 위험 추적

## 주요 스크립트

### 1. `prowler_isms_2025.py` - 통합 자산 식별 및 위험 관리

ISMS-P 2025 가이드에 맞춘 종합적인 자산 식별 및 위험 평가 시스템입니다.

**주요 기능:**
- AWS 자산 자동 식별 (EC2, S3, RDS, Lambda 등)
- 자산 중요도 평가 (CIA 기준)
- Prowler 보안 점검 통합
- 위험 등급 자동 부여 (Critical, High, Medium, Low)
- 위험 평가 보고서 생성

**사용법:**
```bash
# 1. AWS SSO 로그인 (필수)
aws sso login --profile twodragon

# 2. 기본 실행 (프로필: twodragon, 리전: ap-northeast-2)
python prowler_isms_2025.py

# 3. 환경 변수로 설정 변경 (선택적)
export AWS_PROFILE=twodragon
export AWS_REGION=ap-northeast-2
export ISMS_OUTPUT_DIR=./output
python prowler_isms_2025.py
```

**출력:**
- `isms_risk_report_YYYYMMDD_HHMMSS.json`: 위험 평가 보고서 (JSON)
- `prowler_scan_YYYYMMDD_HHMMSS.json`: Prowler 스캔 결과

### 2. `risk_dashboard.py` - 위험 관리 대시보드 생성

위험 평가 보고서를 기반으로 시각적인 HTML 대시보드를 생성합니다.

**사용법:**
```bash
# 보고서 파일로부터 대시보드 생성
python risk_dashboard.py isms_risk_report_20241201_120000.json

# 출력 파일 지정
python risk_dashboard.py isms_risk_report_20241201_120000.json -o dashboard.html
```

**대시보드 기능:**
- 위험 등급별 통계 (Critical, High, Medium, Low)
- 위험 점수 분포 차트
- 자산별 위험 평가 상세 테이블
- 시각적 위험 등급 표시

### 3. `prowler-trivy-scan.py` - Prowler & Trivy 통합 스캔

Prowler와 Trivy를 통합하여 AWS 인프라 및 컨테이너 이미지 보안을 점검합니다.

**사용법:**
```bash
# 1. AWS SSO 로그인 (필수)
aws sso login --profile twodragon

# 2. 스캔 실행
python prowler-trivy-scan.py
```

## 설치 및 설정

### 1. 의존성 설치

```bash
# 기본 의존성
pip install -r ../requirements.txt

# Prowler 설치
pip install prowler

# Trivy 설치 (선택적)
# macOS
brew install trivy

# Linux
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

### 2. AWS SSO 로그인 및 프로필 설정

이 프로젝트는 **AWS SSO (Single Sign-On)**와 **프로필 기반 인증**을 사용합니다.

#### AWS SSO 설정

```bash
# 1. AWS SSO 로그인
aws sso login --profile twodragon

# 2. 프로필 확인 (~/.aws/config 파일)
cat ~/.aws/config

# 예시 설정:
# [profile twodragon]
# sso_start_url = https://your-sso-portal.awsapps.com/start
# sso_region = ap-northeast-2
# sso_account_id = 123456789012
# sso_role_name = YourRoleName
# region = ap-northeast-2
# output = json
```

#### 환경 변수 설정 (선택적)

```bash
# AWS 프로필 설정 (기본값: twodragon)
export AWS_PROFILE=twodragon

# AWS 리전 설정 (기본값: ap-northeast-2)
export AWS_REGION=ap-northeast-2

# 출력 디렉토리
export ISMS_OUTPUT_DIR=./output
```

**참고:** 
- 기본 프로필은 `twodragon`으로 설정되어 있습니다
- 프로필을 변경하려면 `AWS_PROFILE` 환경 변수를 설정하거나 `~/.aws/config`에서 다른 프로필을 사용하세요
- SSO 세션이 만료되면 `aws sso login --profile twodragon`을 다시 실행하세요

### 3. 환경 변수 설정

```bash
# AWS 설정 (기본값 사용 시 생략 가능)
export AWS_PROFILE=twodragon  # 기본값: twodragon
export AWS_REGION=ap-northeast-2  # 기본값: ap-northeast-2

# 출력 디렉토리
export ISMS_OUTPUT_DIR=./output

# 로깅 레벨
export ISMS_LOG_LEVEL=INFO
```

### 4. Prowler 설치 확인

Prowler는 [공식 GitHub 저장소](https://github.com/prowler-cloud/prowler)를 참고하여 설치합니다.

```bash
# Prowler 설치 확인
prowler -v

# Prowler 버전 확인 (Python 3.9 이상, 3.13 미만 필요)
python3 --version

# Prowler 설치 (PyPI)
pip install prowler

# 또는 GitHub에서 직접 설치
git clone https://github.com/prowler-cloud/prowler
cd prowler
poetry install
```

## ISMS-P 2025 가이드 반영 사항

### 1. 자산 식별 및 중요도 평가

- **자동 자산 식별**: AWS API를 통한 자산 자동 수집
- **CIA 기준 평가**: 기밀성, 무결성, 가용성 기준 중요도 평가
- **태그 기반 분류**: AWS 태그를 활용한 자산 분류

### 2. 위험 평가 및 등급 부여

- **위험 점수 계산**: 자산 중요도와 보안 취약점을 종합한 위험 점수 (0-100)
- **위험 등급 분류**:
  - Critical (80점 이상): 즉시 조치 필요
  - High (60-79점): 우선 조치 필요
  - Medium (40-59점): 계획적 조치 필요
  - Low (20-39점): 모니터링 필요
  - Info (20점 미만): 정보성

### 3. 클라우드 환경 보안 강화

- **데이터 주권 준수**: 리전별 자산 식별 및 관리
- **암호화 점검**: Prowler를 통한 암호화 설정 자동 점검
- **접근 제어 점검**: IAM 정책 및 보안 그룹 설정 점검

### 4. AI/머신러닝 데이터 처리 보안

- **데이터 분류 태그**: 자산별 데이터 분류 태그 확인
- **비식별화 처리**: 개인정보 처리 자산 식별
- **보안 관리체계**: AI/ML 관련 자산의 보안 설정 점검

## 워크플로우

### 1. 자산 식별 단계

```python
from prowler_isms_2025 import ProwlerISMS2025
from utils.config import Config

config = Config.from_env()
assessor = ProwlerISMS2025(config)

# 자산 식별
assets = assessor.identify_assets()
```

### 2. 보안 점검 단계

```python
# Prowler 스캔 실행
prowler_output = assessor.run_prowler_scan(
    output_format='json',
    compliance_framework='cis'
)

# 결과 파싱
findings = assessor.parse_prowler_results(prowler_output)
```

### 3. 위험 평가 단계

```python
# 위험 평가
assessments = assessor.assess_risks(assets, findings)

# 보고서 생성
report_file = assessor.generate_risk_report(
    assessments, assets, findings
)
```

### 4. 대시보드 생성

```bash
python risk_dashboard.py isms_risk_report_20241201_120000.json
```

## 자동화 및 스케줄링

### Cron 작업 설정

```bash
# 매주 월요일 오전 9시에 실행
0 9 * * 1 cd /path/to/ISMS/isms-p-cloud-audit && /usr/bin/python3 prowler_isms_2025.py >> /var/log/isms.log 2>&1
```

### Lambda 함수로 실행

스크립트를 Lambda 함수로 변환하여 EventBridge로 정기 실행할 수 있습니다.

## 보고서 분석

### JSON 보고서 구조

```json
{
  "report_metadata": {
    "generated_at": "2024-12-01T12:00:00",
    "report_type": "ISMS-P 2025 Risk Assessment",
    "total_assets": 50,
    "total_findings": 120
  },
  "summary": {
    "critical_risks": 5,
    "high_risks": 15,
    "medium_risks": 30,
    "low_risks": 10,
    "average_risk_score": 45.5
  },
  "assets": [...],
  "assessments": [...],
  "findings": [...]
}
```

### 위험 등급별 조치 우선순위

1. **Critical (즉시 조치)**
   - 보안 정책 위반
   - 암호화 미설정
   - 퍼블릭 액세스 허용

2. **High (우선 조치)**
   - 로깅 미설정
   - 버전 관리 미설정
   - 백업 미설정

3. **Medium (계획적 조치)**
   - 태그 미설정
   - 모니터링 알림 미설정

4. **Low (모니터링)**
   - 최적화 권장 사항
   - 정보성 알림

## 문제 해결

### AWS SSO 관련 오류

**"SSO session expired" 오류:**
```bash
# 해결: 다시 로그인
aws sso login --profile twodragon
```

**"Profile not found" 오류:**
```bash
# 해결: ~/.aws/config 파일 확인 및 설정
cat ~/.aws/config

# 프로필이 없으면 추가
aws configure sso --profile twodragon
```

**자세한 내용:** [`AWS_SSO_SETUP.md`](AWS_SSO_SETUP.md) 참조

### Prowler 설치 오류

```bash
# Python 버전 확인 (3.9 이상, 3.13 미만 필요)
python3 --version

# Prowler 재설치
pip uninstall prowler
pip install prowler

# Prowler 공식 문서 참고
# https://github.com/prowler-cloud/prowler
```

### AWS 권한 오류

필요한 IAM 권한 (SSO 역할에 할당되어 있어야 함):
- `ec2:DescribeInstances`
- `s3:ListBuckets`, `s3:GetBucket*`
- `rds:DescribeDBInstances`
- `lambda:ListFunctions`
- `iam:ListRoles`, `iam:GetRolePolicy`
- `sts:GetCallerIdentity` (인증 확인용)

### Prowler 실행 시 인증 오류

```bash
# 해결 1: 프로필 명시적으로 지정
prowler aws --profile twodragon --region ap-northeast-2

# 해결 2: 환경 변수 설정
export AWS_PROFILE=twodragon
prowler aws

# 해결 3: SSO 세션 확인
aws sts get-caller-identity --profile twodragon
```

### 메모리 부족 오류

대량의 자산이 있는 경우:
- 서비스별로 나누어 실행
- 배치 처리로 분할 실행

## 참고 자료

- [Prowler 공식 문서](https://docs.prowler.com)
- [Prowler GitHub 저장소](https://github.com/prowler-cloud/prowler)
- [AWS SSO 사용자 가이드](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)
- [AWS CLI SSO 설정](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)
- [ISMS-P 인증 가이드](https://isms.go.kr)
- [AWS 보안 모범 사례](https://aws.amazon.com/security/best-practices/)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.
