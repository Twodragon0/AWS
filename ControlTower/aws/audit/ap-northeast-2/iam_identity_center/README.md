# IAM Identity Center Configuration for c_security Group

이 모듈은 AWS IAM Identity Center (이전 AWS SSO)를 사용하여 `c_security` 그룹에 대한 접근 권한을 관리합니다.

## 개요

이 구성은 다음을 제공합니다:

- **Production 환경 권한 세트**: 보안 모니터링 및 감사 접근
- **Development 환경 권한 세트**: 보안 테스트 및 문제 해결 접근
- **관리자 접근 권한 세트**: 감사 계정에 대한 전체 관리자 권한

## 현재 구성

### 계정 할당

- **Audit 계정** (`617558666252`): `c_security` 그룹에 관리자 권한 할당

### Permission Sets

1. **pset_prd_c_security**: Production 환경용 보안 권한
2. **pset_dev_c_security**: Development 환경용 보안 권한
3. **pset_c_administrator_access**: 관리자 접근 권한 (감사 계정 전용)

## 보안 모범 사례

### 세션 지속 시간

- **표준 권한**: 4시간 (PT4H)
- **관리자 권한**: 2시간 (PT2H) - 보안 강화

### 최소 권한 원칙

- Production 환경: 읽기 전용 + 보안 감사 권한
- Development 환경: 읽기 전용 + 문제 해결 권한
- Audit 계정: 관리자 권한 (필요시에만 사용)

### 태깅

모든 리소스에 다음 태그가 적용됩니다:

- `ManagedBy`: Terraform
- `Environment`: production/development/audit
- `PermissionLevel`: security-team/administrator
- `Purpose`: security-monitoring/security-testing/audit-and-compliance
- `Compliance`: ISMS-P
- `CostCenter`: security

## 사용 방법

### 초기화

```bash
terraform init
```

### 계획 확인

```bash
terraform plan
```

### 적용

```bash
terraform apply
```

### 비용 추정

```bash
infracost breakdown --path .
```

**참고**: IAM Identity Center는 무료 서비스입니다. 추가 비용이 발생하지 않습니다.

## 변수

주요 변수는 `variables.tf`에 정의되어 있습니다:

- `common_tags`: 공통 태그
- `session_duration`: 표준 세션 지속 시간 (기본값: PT4H)
- `administrator_session_duration`: 관리자 세션 지속 시간 (기본값: PT2H)

## 출력

`outputs.tf`에서 다음 정보를 확인할 수 있습니다:

- Permission Set ARNs
- Permission Set IDs
- 계정 할당 정보
- 보안 구성 요약

## 향후 확장

Production 및 Development 계정에 권한을 할당하려면:

1. `locals.tf`에서 계정 ID 추가
2. `main.tf`의 `account_assignments` 섹션에서 주석 해제 및 구성

## 참고 자료

- [AWS IAM Identity Center 문서](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)
- [AWS Control Tower 문서](https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html)
- [Terraform AWS Provider 문서](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

