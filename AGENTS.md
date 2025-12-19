# AGENTS.md

이 파일은 AWS 인프라 자동화 저장소에서 AI 코딩 에이전트가 작업할 때 참고할 가이드입니다.

## 프로젝트 개요

이 저장소는 AWS 인프라를 Terraform과 AWS CDK를 사용하여 관리하는 멀티 프로젝트 저장소입니다. 주요 구성 요소:

- **Terraform 기반 인프라**: EC2, EKS, ControlTower, CloudFront, VPC 등
- **AWS CDK 프로젝트**: TypeScript로 작성된 Bedrock, networking-costs-calculator
- **Python Lambda 함수**: 보안 모니터링, API 감사, 자동화 스크립트
- **보안 스캔**: CodeQL, TFSec, Checkov, Trivy를 통한 자동 보안 검사

## 개발 환경 설정

### 사전 요구 사항

- **Terraform**: 인프라 코드 관리
- **AWS CLI**: AWS 리소스 관리
- **Python 3.x**: Lambda 함수 및 스크립트 실행
- **Node.js 20**: CDK 프로젝트 빌드
- **AWS CDK**: TypeScript 프로젝트 배포

### 프로젝트 구조 파악

```bash
# Terraform 프로젝트 찾기
find . -name "*.tf" -type f | head -20

# CDK 프로젝트 찾기
find . -name "cdk.json" -type f

# Python Lambda 함수 찾기
find . -name "lambda_function.py" -type f
find . -name "requirements.txt" -type f
```

## Terraform 작업 가이드

### Terraform 프로젝트 위치

- `EC2/terraform/` - EC2 인프라 및 Lambda 모니터링
- `EKS/` - Kubernetes 클러스터 인프라
- `ControlTower/aws/audit/` - AWS Control Tower 감사 설정
- `Cloudfront/s3-cloudfront-cdn/` - CloudFront 및 S3 설정
- `VPC/` - VPC 및 보안 그룹 관리

### Terraform 명령어

```bash
# 특정 디렉토리로 이동
cd EC2/terraform

# Terraform 초기화 (백엔드 설정 확인 필요)
terraform init

# 계획 확인
terraform plan

# 적용 (주의: 실제 리소스 생성/변경)
terraform apply

# 상태 확인
terraform show

# 특정 리소스만 타겟팅
terraform apply -target=module.lambda
```

### Terraform 모듈 구조

- `EC2/terraform/modules/lambda/` - Lambda 함수 모듈
- `EC2/terraform/modules/dynamodb/` - DynamoDB 상태 잠금 모듈
- `EC2/terraform/modules/vpc_endpoints/` - VPC 엔드포인트 모듈
- `EKS/modules/` - EKS 관련 모듈

### Terraform 백엔드 설정

- 백엔드 설정은 `backend.tf` 파일에 정의됨
- 초기 설정은 `initial_setup/` 디렉토리에서 S3 버킷 및 DynamoDB 테이블 생성
- 백엔드 변경 시 `terraform init -migrate-state` 필요

## AWS CDK 작업 가이드

### CDK 프로젝트 위치

- `Bedrock/` - Amazon Bedrock Knowledge Base Slack Bot
- `networking-costs-calculator/backend/` - 네트워크 비용 계산기 백엔드
- `networking-costs-calculator/frontend/` - 네트워크 비용 계산기 프론트엔드

### CDK 명령어

```bash
# Bedrock 프로젝트 작업
cd Bedrock
npm install
npm run build
npm test
cdk synth
cdk deploy

# networking-costs-calculator 백엔드 작업
cd networking-costs-calculator/backend
npm install
npm run build
npm test
cdk synth
cdk deploy

# networking-costs-calculator 프론트엔드 작업
cd networking-costs-calculator/frontend
npm install
npm run build
```

### CDK 빌드 및 테스트

- TypeScript 컴파일: `npm run build` 또는 `tsc`
- 테스트 실행: `npm test` (Jest 사용)
- CDK 합성: `cdk synth` (실제 배포 전 확인)
- CDK 배포: `cdk deploy` (주의: 실제 AWS 리소스 생성)

## Python Lambda 함수 작업 가이드

### Lambda 함수 위치

- `Lambda/` - 다양한 Lambda 함수들
  - `AWS-API-Monitor/` - CloudTrail 모니터링
  - `SSM/` - SSM 관련 함수
- `EC2/terraform/modules/lambda/` - Terraform으로 관리되는 Lambda
- `Bedrock/lambda/` - Bedrock 프로젝트의 Lambda 함수
- `VPC/` - Okta IP 범위 관리 Lambda

### Python 환경 설정

```bash
# 가상 환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# Lambda 함수 패키징 (EC2 프로젝트)
cd EC2/terraform
./build_lambda.sh
```

### Lambda 함수 테스트

```bash
# 로컬 테스트 스크립트 실행
python EC2/scripts/aws_monitor_local.py

# Lambda 함수 코드 검증
python -m py_compile lambda_function.py
```

## 보안 및 코드 품질

### 자동 보안 스캔

이 저장소는 여러 보안 스캔 도구를 사용합니다:

1. **CodeQL**: Python 및 JavaScript 코드 보안 분석
2. **TFSec**: Terraform 코드 보안 검사
3. **Checkov**: Terraform 인프라 보안 검사
4. **Trivy**: 취약점 스캔
5. **Secret Scanning**: TruffleHog 및 Gitleaks를 통한 시크릿 검사

### 보안 스캔 실행

```bash
# GitHub Actions에서 자동 실행되지만, 로컬에서도 가능:

# TFSec 실행
docker run --rm -it -v "$(pwd):/src" aquasec/tfsec /src

# Checkov 실행
checkov -d . --framework terraform

# Trivy 실행
trivy fs --security-checks vuln,config .
```

### 코드 품질 확인

- **Python**: PEP 8 스타일 가이드 준수
- **TypeScript**: ESLint 및 TypeScript 컴파일러 검사
- **Terraform**: `terraform fmt` 및 `terraform validate` 실행

## 테스트 가이드

### Terraform 테스트

```bash
# Terraform 검증
terraform validate

# Terraform 포맷팅
terraform fmt -check
terraform fmt -write

# Terraform 계획 확인 (실제 변경 없이)
terraform plan -out=tfplan
```

### CDK 테스트

```bash
# Bedrock 프로젝트 테스트
cd Bedrock
npm test

# networking-costs-calculator 백엔드 테스트
cd networking-costs-calculator/backend
npm test
```

### Python 테스트

```bash
# Python 스크립트 실행
python Lambda/Config_lambda_function.py

# ISMS 스크립트 실행
python ISMS/ec2_info.py
```

## Git 워크플로우

### 브랜치 전략

- `main` 또는 `master` 브랜치에 직접 푸시하지 않음
- 기능 브랜치에서 작업 후 Pull Request 생성
- PR 제목 형식: `[프로젝트명] 제목` (예: `[EC2] Lambda 함수 업데이트`)

### 커밋 전 체크리스트

```bash
# Terraform 프로젝트
terraform fmt
terraform validate

# CDK 프로젝트
npm run build
npm test
npm run lint  # 있는 경우

# Python 프로젝트
python -m py_compile *.py
# 또는
flake8 *.py  # 설치된 경우
```

## AWS 리소스 접근

### AWS Identity Center (SSO) 사용

- 대부분의 프로젝트는 AWS Identity Center를 통한 SSO 인증 사용
- `ControlTower/aws/audit/ap-northeast-2/iam_identity_center/`에서 IAM Identity Center 설정 관리

### AWS 리전

- 기본 리전: `ap-northeast-2` (서울)
- 리전별 설정은 각 프로젝트의 `variables.tf` 또는 설정 파일 확인

## 문제 해결

### 일반적인 문제

1. **Terraform 백엔드 오류**: `backend.tf` 파일의 S3 버킷 및 DynamoDB 테이블 확인
2. **CDK 배포 실패**: `cdk synth`로 먼저 검증
3. **Lambda 함수 오류**: 로컬에서 Python 스크립트로 먼저 테스트
4. **권한 오류**: IAM 역할 및 정책 확인

### 로그 확인

```bash
# CloudWatch Logs 확인 (AWS CLI)
aws logs tail /aws/lambda/function-name --follow

# Terraform 상태 확인
terraform state list
terraform state show <resource_name>
```

## 주의사항

- **실제 AWS 리소스 생성/변경**: `terraform apply` 및 `cdk deploy` 실행 시 주의
- **비용**: 리소스 생성 시 AWS 비용 발생 가능
- **보안**: 시크릿 및 자격 증명은 절대 커밋하지 않음
- **백엔드 상태**: Terraform 상태 파일은 S3에 저장되며, 동시 작업 시 충돌 주의

## 추가 리소스

- AWS 공식 문서: https://docs.aws.amazon.com/
- Terraform 문서: https://www.terraform.io/docs
- AWS CDK 문서: https://docs.aws.amazon.com/cdk/
- 프로젝트별 README 파일 참조:
  - `EC2/Readme.md`
  - `Bedrock/readme.md`
  - `Lambda/README.md`
  - `ControlTower/Readme.md`

