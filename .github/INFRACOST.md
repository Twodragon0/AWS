# Infracost 설정 가이드

이 리포지토리는 [Infracost](https://www.infracost.io/)를 사용하여 Terraform 인프라의 비용을 추정합니다.

## 개요

Infracost는 Terraform 코드를 분석하여 AWS 리소스의 월별 예상 비용을 계산합니다. 이를 통해 인프라 변경사항이 비용에 미치는 영향을 사전에 파악할 수 있습니다.

## 설정 방법

### 1. Infracost API 키 발급

1. [Infracost Cloud](https://www.infracost.io/docs/cloud/)에 가입하거나 로그인
2. Settings > API Keys에서 API 키 생성
3. GitHub 저장소의 Settings > Secrets and variables > Actions에 `INFRACOST_API_KEY` 추가

### 2. GitHub Actions 워크플로우

이 리포지토리에는 두 가지 Infracost 워크플로우가 포함되어 있습니다:

#### `infracost.yml` - Pull Request 비용 분석
- Pull Request 생성/업데이트 시 자동 실행
- 변경된 Terraform 파일에 대해 비용 추정
- PR 코멘트로 비용 정보 자동 표시

#### `infracost-schedule.yml` - 주간 비용 리포트
- 매주 월요일 자동 실행
- 모든 Terraform 프로젝트의 비용 분석
- 결과를 Artifact로 저장

## 지원되는 프로젝트

다음 Terraform 프로젝트가 Infracost로 분석됩니다:

1. **EC2/terraform** - EC2 인프라 (VPC, 서브넷, EC2 인스턴스 등)
2. **EKS** - EKS 클러스터 인프라
3. **Cloudfront/s3-cloudfront-cdn** - CloudFront 및 S3 CDN 설정
4. **ControlTower/aws/audit** - Control Tower 감사 설정

## 사용 방법

### Pull Request에서 비용 확인

1. Terraform 파일을 변경하는 PR 생성
2. GitHub Actions가 자동으로 실행
3. PR 코멘트에 비용 정보가 자동으로 표시됨

### 로컬에서 실행

```bash
# Infracost 설치
brew install infracost/tap/infracost

# API 키 설정 (선택사항, Cloud 사용 시)
export INFRACOST_API_KEY=your-api-key

# 특정 프로젝트 분석
cd EC2/terraform
terraform init
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json
infracost breakdown --path tfplan.json

# 또는 직접 Terraform 파일 분석
infracost breakdown --path .
```

### 비용 비교

```bash
# 현재 상태와 변경사항 비교
infracost diff --path EC2/terraform
```

## 비용 최적화 팁

1. **사용하지 않는 리소스 제거**: Infracost 리포트에서 0 USD로 표시되는 리소스 확인
2. **인스턴스 타입 최적화**: EC2 인스턴스 타입 변경 시 비용 영향 확인
3. **스토리지 최적화**: S3 스토리지 클래스 및 EBS 볼륨 타입 검토
4. **예약 인스턴스**: 장기 운영 시 Reserved Instances 고려

## 문제 해결

### API 키 오류
- GitHub Secrets에 `INFRACOST_API_KEY`가 올바르게 설정되었는지 확인
- API 키가 유효한지 확인

### Terraform 초기화 실패
- Terraform 백엔드 설정 확인
- 필요한 변수 파일 존재 여부 확인
- AWS 자격 증명 설정 확인

### 비용 추정이 0으로 표시되는 경우
- 리소스가 Infracost에서 지원되지 않을 수 있음
- Terraform plan이 올바르게 생성되었는지 확인

## 참고 자료

- [Infracost 문서](https://www.infracost.io/docs/)
- [Infracost GitHub Actions](https://github.com/infracost/actions)
- [AWS 가격 정보](https://aws.amazon.com/pricing/)


