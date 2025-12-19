# 저장소 설정 가이드

이 가이드는 저장소를 처음 설정하거나 새로운 개발 환경을 구성할 때 참고하는 문서입니다.

## 📋 목차

1. [사전 요구 사항](#사전-요구-사항)
2. [저장소 클론 및 설정](#저장소-클론-및-설정)
3. [Pre-commit Hook 설정](#pre-commit-hook-설정)
4. [개발 환경 설정](#개발-환경-설정)
5. [보안 설정](#보안-설정)
6. [문제 해결](#문제-해결)

## 사전 요구 사항

### 필수 도구

- **Git** >= 2.30
- **Terraform** >= 1.0
- **AWS CLI** >= 2.0
- **Python** >= 3.9
- **Node.js** >= 20
- **AWS CDK** >= 2.0

### 선택 도구

- **pre-commit** (권장)
- **Docker** (보안 스캔 도구 실행용)

## 저장소 클론 및 설정

```bash
# 저장소 클론
git clone <repository-url>
cd AWS

# 원격 저장소 확인
git remote -v
```

## Pre-commit Hook 설정

Pre-commit hook은 커밋 전에 자동으로 코드 검사를 수행합니다.

### 설치 방법

```bash
# pre-commit 설치
pip install pre-commit

# 또는 Homebrew (macOS)
brew install pre-commit

# Hook 설치
pre-commit install

# 모든 파일에 대해 한 번 실행 (선택사항)
pre-commit run --all-files
```

### Pre-commit Hook 기능

- ✅ Terraform 포맷팅 및 검증
- ✅ Python 코드 포맷팅 (Black)
- ✅ 시크릿 검사
- ✅ YAML/JSON 검증
- ✅ Markdown 린팅
- ✅ Shell 스크립트 검사

### 수동 실행

```bash
# 특정 파일 검사
pre-commit run --files <file-path>

# 특정 hook만 실행
pre-commit run terraform_fmt
pre-commit run detect-secrets
```

## 개발 환경 설정

### Terraform 설정

```bash
# Terraform 버전 확인
terraform version

# 특정 프로젝트로 이동
cd EC2/terraform

# 초기화
terraform init

# 백엔드 설정 확인
cat backend.tf
```

### AWS CDK 설정

```bash
# CDK 프로젝트로 이동
cd Bedrock

# 의존성 설치
npm install

# CDK 부트스트랩 (최초 1회)
cdk bootstrap

# 빌드
npm run build

# 테스트
npm test
```

### Python 환경 설정

```bash
# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 보안 설정

### AWS 자격 증명 설정

**⚠️ 중요**: 절대 자격 증명을 코드에 하드코딩하지 마세요!

```bash
# AWS CLI 설정
aws configure

# 또는 AWS Identity Center (SSO) 사용
aws configure sso
```

### 시크릿 관리

- ✅ **AWS Secrets Manager** 사용
- ✅ **SSM Parameter Store** 사용
- ✅ **환경 변수** 사용
- ❌ **코드에 하드코딩** 금지

### Git 시크릿 검사

```bash
# detect-secrets로 시크릿 검사
detect-secrets scan --baseline .secrets.baseline

# 새로운 시크릿 검사
detect-secrets scan --baseline .secrets.baseline --force-use-all-processors
```

## 문제 해결

### Pre-commit Hook이 작동하지 않는 경우

```bash
# Hook 재설치
pre-commit uninstall
pre-commit install

# 권한 확인
chmod +x .git/hooks/pre-commit
```

### Terraform 백엔드 오류

```bash
# 백엔드 재초기화
terraform init -reconfigure

# 백엔드 마이그레이션
terraform init -migrate-state
```

### CDK 빌드 오류

```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install

# TypeScript 컴파일 확인
npm run build
```

### Python 가상 환경 문제

```bash
# 가상 환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 추가 리소스

- [AGENTS.md](./AGENTS.md) - AI 코딩 에이전트 가이드
- [REPOSITORY_AUDIT_REPORT.md](./REPOSITORY_AUDIT_REPORT.md) - 저장소 검토 리포트
- [.github/SECRET_SCANNING.md](./.github/SECRET_SCANNING.md) - 시크릿 스캔 가이드

---

**마지막 업데이트**: 2025-01-27

