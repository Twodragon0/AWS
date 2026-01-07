# 저장소 통합 및 마이그레이션 내역

이 문서는 `aws-iam-policies` 저장소와 `aws-tools` 저장소에서 `aws-devsecops-infrastructure` 저장소로 통합된 내역을 정리합니다.

## 📋 개요

### 통합된 저장소
- **aws-iam-policies**: IAM 정책 및 보안 표준
- **aws-tools**: Lambda 함수 및 보안 도구
- **aws-devsecops-infrastructure**: 통합된 메인 저장소

---

## 🔄 aws-iam-policies에서 옮긴 내역

### 1. IAM 정책 파일 이동 (커밋: `867685de`)

다음 파일들이 루트 디렉토리에서 `IAM/` 디렉토리로 이동되었습니다:

| 원본 경로 | 이동 경로 | 설명 |
|---------|---------|------|
| `CodeCommitReadOnly.json` | `IAM/CodeCommitReadOnly.json` | CodeCommit 읽기 전용 정책 |
| `Console_MFA_IP.json` | `IAM/Console_MFA_IP.json` | 콘솔 MFA 및 IP 제한 정책 |
| `SecretsManager-KMS-Tag.json` | `IAM/SecretsManager-KMS-Tag.json` | Secrets Manager 및 KMS 태그 기반 정책 |
| `README.md` | `IAM/README.md` | IAM 정책 문서 |

### 2. 현재 IAM 정책 파일 구조

```
IAM/
├── CodeCommitReadOnly.json          # CodeCommit 읽기 전용 접근 정책
├── Console_MFA_IP.json              # 콘솔 접근 MFA 및 IP 제한 정책
├── SecretsManager-KMS-Tag.json      # Secrets Manager 및 KMS 태그 기반 정책
└── README.md                         # IAM 정책 사용 가이드
```

### 3. IAM 정책 파일 상세

#### CodeCommitReadOnly.json
- **용도**: CodeCommit 리포지토리에 대한 읽기 전용 접근 권한
- **주요 권한**:
  - CodeCommit Git Pull 작업
  - CodeCommit 리소스 조회 및 나열
  - CloudWatch Events 규칙 읽기
  - SNS 구독 정보 조회
  - Lambda 함수 목록 조회
  - IAM 사용자 정보 조회
- **조건**: VPC 엔드포인트(`vpce-*`)에서만 접근 허용

#### Console_MFA_IP.json
- **용도**: AWS Management Console 접근 시 MFA 및 IP 제한
- **주요 기능**:
  - IAM 사용자 계정 관리
  - 비밀번호 변경
  - 로그인 프로필 생성
  - MFA 디바이스 관리

#### SecretsManager-KMS-Tag.json
- **용도**: 리소스 태그 기반 Secrets Manager 및 KMS 접근 제어
- **주요 기능**:
  - 태그 기반 조건부 접근
  - Secrets Manager 시크릿 접근
  - KMS 키 관리

### 4. 추가 정책 파일

#### Lambda/SSM 관련 정책
- **위치**: `Lambda/SSM/IAM_policy.json`
- **용도**: SSM Session Manager 접근을 위한 IAM 정책
- **주요 권한**:
  - `ssm:StartSession`: SSM 세션 시작
  - `ssm:SendCommand`: SSM 명령 실행
  - `ssm:TerminateSession`: SSM 세션 종료
  - `ssm:ResumeSession`: SSM 세션 재개
  - `kms:GenerateDataKey`: KMS 데이터 키 생성

#### ControlTower 관련 정책
- **위치**: `ControlTower/aws/audit/ap-northeast-2/iam/policy_pset_c_security.json`
- **커밋**: `1d752145` (Create policy_pset_c_security.json)
- **용도**: ControlTower 보안 권한 세트 정책

---

## 🛠️ aws-tools에서 통합된 내역

### 1. Lambda 함수 통합

#### AWS-API-Monitor
**위치**: `Lambda/AWS-API-Monitor/`

**주요 Lambda 함수**:
- `cloudtrail_audit_lambda_function.py`: CloudTrail 로그 감사
- `sg_lambda_function.py`: 보안 그룹 모니터링
- `kms_lambda_function.py`: KMS 키 모니터링

**기능**:
- 실시간 AWS API 활동 모니터링
- CloudTrail 로그 감사
- 보안 그룹 및 KMS 키 모니터링
- CloudWatch Events 통합
- SNS 알림

#### SSM (Systems Manager)
**위치**: `Lambda/SSM/`

**파일**:
- `lambda_function.py`: SSM 설정 Lambda 함수
- `IAM_policy.json`: SSM 접근을 위한 IAM 정책
- `SCP_Policy.json`: Service Control Policy (SCP)
- `readme.md`: SSM 구현 가이드

**SCP_Policy.json 상세**:
```json
{
   "Version": "2012-10-17",
   "Statement": [
      {
         "Effect": "Deny",
         "Action": [
            "ssm:StartSession",
            "ssm:SendCommand"
         ],
         "Resource": "*",
         "Condition": {
            "ArnLike": {
               "aws:PrincipalArn": [
                  "arn:aws:iam::(account-ID):user/*",
                  "arn:aws:iam::(account-ID):group/*",
                  "arn:aws:iam::(account-ID):role/*"
               ]
            }
         }
      }
   ]
}
```

**용도**: 조직 레벨에서 SSM 접근을 제한하는 SCP 정책

#### 기타 Lambda 함수
- `config_lambda_function.py`: AWS Config 통합
- `guardduty_lambda_function.py`: GuardDuty 통합

### 2. 보안 표준 (security_standards)

#### IAM 보안 가이드
**위치**: `security_standards/IAM/Readme.md`

**주요 내용**:
- **정책명**: IT Infrastructure Security Maintenance Policy
- **카테고리**: Information Protection
- **정책 관리자**: Security Strategy Team

**핵심 정책 사항**:
1. **정기 검토 및 관리**
   - 90일 이상 미사용 IAM 계정 및 Access Key 삭제 또는 비활성화
   - 회사 보안 정책 위반 시 즉시 삭제
   - 퇴사 또는 직무 변경으로 불필요한 계정 삭제

2. **손실 또는 노출 대응**
   - IAM 계정 또는 Access Key 손실/노출 시 즉시 변경

3. **IAM Access Key 유효 기간**
   - 최대 180일
   - 만료 전 안전성 검토 및 변경/연장 여부 결정

**보안 검토 가이드라인**:
- 정기 감사 수행
- 최소 권한 원칙 적용
- 모니터링 및 로깅 활성화
- 보안 인식 교육
- 사고 대응 계획 수립

#### Management Console 보안
**위치**: `security_standards/Management_Console/readme.md`

**주요 내용**: AWS Management Console 보안 설정 가이드

#### 클라우드 보안 검토 가이드라인
**위치**: `security_standards/Readme.md`

**주요 내용**:
- AWS, Azure, GCP 보안 고려사항
- 자산 거래 서비스 개발/수정 시 보안 설정
- 외부 조직 전자 거래 통합
- 네트워크 구성 변경
- 인터넷 세그먼트 통합
- 보안 시스템 구현 및 설치
- 고객 개인정보 처리 신규 사업

---

## 📊 통합 상태 비교

### 파일 중복 확인

| 파일 경로 | aws-devsecops-infrastructure | aws-iam-policies | aws-tools | 상태 |
|---------|----------------------------|-----------------|-----------|------|
| `IAM/CodeCommitReadOnly.json` | ✅ | ✅ | ❌ | 동일 |
| `IAM/Console_MFA_IP.json` | ✅ | ✅ | ❌ | 동일 |
| `IAM/SecretsManager-KMS-Tag.json` | ✅ | ✅ | ❌ | 동일 |
| `Lambda/SSM/IAM_policy.json` | ✅ | ✅ | ✅ | 동일 |
| `Lambda/SSM/SCP_Policy.json` | ✅ | ✅ | ✅ | 동일 |
| `Lambda/AWS-API-Monitor/` | ✅ | ✅ | ✅ | 동일 |

### aws-iam-policies 디렉토리 상태

`aws-iam-policies/` 디렉토리는 이전 저장소의 전체 백업/복사본으로 보입니다:
- 전체 프로젝트 구조가 포함되어 있음
- 최신 변경사항은 루트 디렉토리에 반영됨
- 참고용으로 유지 가능

---

## 🔍 주요 차이점 및 추가 사항

### 1. aws-tools에만 있는 내용

#### security_standards 디렉토리
- `security_standards/IAM/Readme.md`: 상세한 IAM 보안 정책 가이드
- `security_standards/Management_Console/readme.md`: Management Console 보안 가이드
- `security_standards/Readme.md`: 클라우드 보안 검토 가이드라인

**권장 조치**: 이 내용들을 `aws-devsecops-infrastructure` 저장소로 통합 고려

### 2. 파일명 차이

- `aws-tools`: `guardduty_lambda_function.py`
- `aws-devsecops-infrastructure`: `Guardduty_lambda.function.py`

**권장 조치**: 파일명 통일 검토

---

## 📝 통합 권장 사항

### 1. security_standards 통합

`aws-tools/security_standards/` 디렉토리의 내용을 `aws-devsecops-infrastructure`로 통합:

```bash
# 권장 구조
aws-devsecops-infrastructure/
├── security_standards/
│   ├── IAM/
│   │   └── Readme.md
│   ├── Management_Console/
│   │   └── readme.md
│   └── Readme.md
```

### 2. 문서 통합

- `aws-tools/README.md`의 아키텍처 다이어그램 및 설명을 메인 README에 통합
- 보안 표준 문서를 `docs/security_standards/`로 이동 고려

### 3. Lambda 함수 정리

- 파일명 통일 (예: `guardduty_lambda_function.py`)
- 중복 파일 제거
- 공통 의존성 통합

### 4. IAM 정책 정리

- `IAM/` 디렉토리에 모든 IAM 정책 통합
- `Lambda/SSM/IAM_policy.json`을 `IAM/SSM/`으로 이동 고려
- SCP 정책은 `ControlTower/` 또는 별도 `SCP/` 디렉토리로 분리

---

## 🗂️ 최종 권장 구조

```
aws-devsecops-infrastructure/
├── IAM/                              # IAM 정책 (aws-iam-policies에서 통합)
│   ├── CodeCommitReadOnly.json
│   ├── Console_MFA_IP.json
│   ├── SecretsManager-KMS-Tag.json
│   ├── SSM/                          # SSM 관련 정책
│   │   ├── IAM_policy.json
│   │   └── SCP_Policy.json
│   └── README.md
├── Lambda/                           # Lambda 함수 (aws-tools에서 통합)
│   ├── AWS-API-Monitor/
│   ├── SSM/
│   ├── config_lambda_function.py
│   └── guardduty_lambda_function.py
├── security_standards/               # 보안 표준 (aws-tools에서 통합)
│   ├── IAM/
│   ├── Management_Console/
│   └── Readme.md
├── ControlTower/                     # ControlTower 설정
│   └── aws/audit/ap-northeast-2/iam/
│       └── policy_pset_c_security.json
└── docs/                            # 문서
    └── security_standards/           # 보안 표준 상세 문서
```

---

## ✅ 통합 완료 항목

- [x] IAM 정책 파일 이동 (`IAM/` 디렉토리)
- [x] Lambda 함수 통합 (`Lambda/` 디렉토리)
- [x] SSM 정책 파일 통합
- [x] ControlTower 정책 파일 생성

## 🔄 통합 필요 항목

- [ ] `security_standards/` 디렉토리 통합
- [ ] Lambda 함수 파일명 통일
- [ ] 문서 통합 및 정리
- [ ] 중복 파일 제거
- [ ] README 업데이트

---

## 📚 참고 자료

### 관련 문서
- [IAM/README.md](./IAM/README.md) - IAM 정책 사용 가이드
- [Lambda/README.md](./Lambda/README.md) - Lambda 함수 가이드
- [AGENTS.md](./AGENTS.md) - AI 코딩 에이전트 가이드

### 외부 저장소
- **aws-iam-policies**: IAM 정책 원본 저장소 (백업용)
- **aws-tools**: Lambda 함수 및 보안 도구 원본 저장소

---

**작성일**: 2025-01-27  
**작성자**: DevSecOps Team  
**최종 업데이트**: 2025-01-27

