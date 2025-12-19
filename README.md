# AWS Infrastructure Automation Repository

이 저장소는 Terraform과 AWS CDK를 사용하여 AWS 인프라를 자동화하고 관리하는 멀티 프로젝트 저장소입니다.

## 📋 목차

- [개요](#개요)
- [프로젝트 구조](#프로젝트-구조)
- [빠른 시작](#빠른-시작)
- [주요 프로젝트](#주요-프로젝트)
- [보안](#보안)
- [기여 가이드](#기여-가이드)
- [참고 자료](#참고-자료)

## 🎯 개요

이 저장소는 다양한 AWS 서비스와 인프라를 코드로 관리하는 Infrastructure as Code (IaC) 프로젝트 모음입니다. 주요 기술 스택:

- **Terraform**: 인프라 프로비저닝 및 관리
- **AWS CDK**: TypeScript 기반 클라우드 인프라 정의
- **Python**: Lambda 함수 및 자동화 스크립트
- **GitHub Actions**: CI/CD 및 보안 스캔 자동화

## 📁 프로젝트 구조

```
AWS/
├── Bedrock/                          # Amazon Bedrock Knowledge Base Slack Bot (CDK)
├── Cloudfront/                       # CloudFront 및 S3 CDN 설정 (Terraform)
├── ControlTower/                    # AWS Control Tower 감사 설정 (Terraform)
├── EC2/                             # EC2 인프라 및 Lambda 모니터링 (Terraform)
├── EKS/                             # Kubernetes 클러스터 인프라 (Terraform)
├── Lambda/                          # Python Lambda 함수들
├── networking-costs-calculator/      # 네트워크 비용 계산기 (CDK)
├── ISMS/                            # ISMS 감사 스크립트 (Python)
├── VPC/                             # VPC 및 보안 그룹 관리 (Terraform)
└── .github/workflows/               # GitHub Actions 워크플로우
```

각 프로젝트의 상세한 설명은 해당 디렉토리의 README 파일을 참조하세요.

## 🚀 빠른 시작

### 사전 요구 사항

- **Terraform** >= 1.0
- **AWS CLI** >= 2.0
- **Python** >= 3.9
- **Node.js** >= 20
- **AWS CDK** >= 2.0

### Terraform 프로젝트 작업

```bash
# 특정 Terraform 프로젝트로 이동
cd EC2/terraform

# 초기화
terraform init

# 계획 확인
terraform plan

# 적용 (주의: 실제 리소스 생성)
terraform apply
```

### CDK 프로젝트 작업

```bash
# Bedrock 프로젝트 예시
cd Bedrock

# 의존성 설치
npm install

# 빌드
npm run build

# 테스트
npm test

# CDK 합성 (배포 전 확인)
cdk synth

# 배포 (주의: 실제 리소스 생성)
cdk deploy
```

자세한 내용은 [AGENTS.md](./AGENTS.md) 파일을 참조하세요.

## 🏗️ 주요 프로젝트

### EC2 Infrastructure
- **위치**: `EC2/terraform/`
- **설명**: VPC, 서브넷, 보안 그룹, EC2 인스턴스 및 Lambda 모니터링
- **문서**: [EC2/Readme.md](./EC2/Readme.md)

### Amazon Bedrock Slack Bot
- **위치**: `Bedrock/`
- **설명**: Amazon Bedrock Knowledge Base를 활용한 Slack 챗봇
- **문서**: [Bedrock/readme.md](./Bedrock/readme.md)

### EKS Cluster
- **위치**: `EKS/`
- **설명**: Kubernetes 클러스터 인프라 자동화
- **문서**: [EKS/README.md](./EKS/) (참고)

### Networking Costs Calculator
- **위치**: `networking-costs-calculator/`
- **설명**: AWS 네트워크 비용 계산 도구
- **문서**: [networking-costs-calculator/README.md](./networking-costs-calculator/README.md)

## 🔒 보안

이 저장소는 여러 보안 스캔 도구를 사용하여 코드 품질과 보안을 자동으로 검사합니다:

- **CodeQL**: 코드 보안 분석
- **TFSec**: Terraform 보안 검사
- **Checkov**: 인프라 보안 검사
- **Trivy**: 취약점 스캔
- **Secret Scanning**: 시크릿 검사

### 보안 가이드라인

- ⚠️ **절대 커밋하지 말 것**: `.tfstate` 파일, `.tfvars` 파일, API 키, 비밀번호
- ✅ **사용 권장**: AWS Secrets Manager, SSM Parameter Store, 환경 변수
- 📖 자세한 내용: [.github/SECRET_SCANNING.md](./.github/SECRET_SCANNING.md)

## 🤝 기여 가이드

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

# Python 프로젝트
python -m py_compile *.py
```

### 코드 스타일

- **Terraform**: `terraform fmt` 자동 포맷팅
- **TypeScript**: ESLint 및 TypeScript 컴파일러 검사
- **Python**: PEP 8 스타일 가이드 준수

## 📚 참고 자료

### 프로젝트 문서
- [AGENTS.md](./AGENTS.md) - AI 코딩 에이전트 가이드
- [REPOSITORY_AUDIT_REPORT.md](./REPOSITORY_AUDIT_REPORT.md) - 저장소 검토 리포트
- [SECURITY_INCIDENT.md](./SECURITY_INCIDENT.md) - 보안 사고 대응 기록

### 외부 문서
- [AWS 공식 문서](https://docs.aws.amazon.com/)
- [Terraform 문서](https://www.terraform.io/docs)
- [AWS CDK 문서](https://docs.aws.amazon.com/cdk/)

## ⚠️ 주의사항

- **실제 AWS 리소스 생성/변경**: `terraform apply` 및 `cdk deploy` 실행 시 주의
- **비용**: 리소스 생성 시 AWS 비용 발생 가능
- **보안**: 시크릿 및 자격 증명은 절대 커밋하지 않음
- **백엔드 상태**: Terraform 상태 파일은 S3에 저장되며, 동시 작업 시 충돌 주의

## 📝 라이선스

각 프로젝트는 개별 라이선스를 가질 수 있습니다. 프로젝트별 LICENSE 파일을 확인하세요.

## 📞 문의

프로젝트 관련 문의사항은 Issues를 통해 제출해주세요.

---

**마지막 업데이트**: 2025-01-27

