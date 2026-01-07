# AWS SSO 설정 가이드

이 가이드는 AWS SSO (Single Sign-On)를 사용하여 ISMS-P 2025 스크립트를 실행하는 방법을 설명합니다.

## 사전 요구 사항

1. **AWS CLI 설치**
   ```bash
   # macOS
   brew install awscli
   
   # Linux
   sudo apt-get install awscli
   
   # 버전 확인
   aws --version
   ```

2. **AWS SSO 접근 권한**
   - 조직의 AWS SSO 포털에 접근 권한이 있어야 합니다
   - 적절한 역할(Role)에 할당되어 있어야 합니다

## AWS SSO 설정

### 1. AWS SSO 프로필 설정

`~/.aws/config` 파일에 다음 내용을 추가합니다:

```ini
[profile twodragon]
sso_start_url = https://your-sso-portal.awsapps.com/start
sso_region = ap-northeast-2
sso_account_id = 123456789012
sso_role_name = YourRoleName
region = ap-northeast-2
output = json
```

**설정 항목 설명:**
- `sso_start_url`: AWS SSO 포털 시작 URL
- `sso_region`: SSO가 설정된 리전
- `sso_account_id`: AWS 계정 ID
- `sso_role_name`: 사용할 IAM 역할 이름
- `region`: 기본 AWS 리전
- `output`: 출력 형식 (json, yaml, text)

### 2. AWS SSO 로그인

```bash
# 프로필을 사용하여 SSO 로그인
aws sso login --profile twodragon

# 로그인 성공 시 브라우저가 열리고 인증을 완료합니다
# 성공 메시지: "Successfully logged into Start URL: https://..."
```

### 3. 로그인 상태 확인

```bash
# 현재 인증된 사용자 정보 확인
aws sts get-caller-identity --profile twodragon

# 출력 예시:
# {
#     "UserId": "AROAXXXXXXXXXXXXXXXXX:user@example.com",
#     "Account": "123456789012",
#     "Arn": "arn:aws:sts::123456789012:assumed-role/YourRoleName/user@example.com"
# }
```

## 스크립트 실행

### 기본 실행

```bash
# 1. AWS SSO 로그인 (필수)
aws sso login --profile twodragon

# 2. 스크립트 실행
cd ISMS/isms-p-cloud-audit
python prowler_isms_2025.py
```

### 환경 변수 설정 (선택적)

```bash
# AWS 프로필 설정 (기본값: twodragon)
export AWS_PROFILE=twodragon

# AWS 리전 설정 (기본값: ap-northeast-2)
export AWS_REGION=ap-northeast-2

# 출력 디렉토리
export ISMS_OUTPUT_DIR=./output

# 스크립트 실행
python prowler_isms_2025.py
```

## SSO 세션 관리

### 세션 만료 확인

AWS SSO 세션은 일반적으로 8-12시간 동안 유효합니다. 세션이 만료되면 다시 로그인해야 합니다.

```bash
# 세션 만료 시 오류 메시지
# "The SSO session associated with this profile has expired or is otherwise invalid"

# 해결 방법: 다시 로그인
aws sso login --profile twodragon
```

### 자동 로그인 스크립트

세션 만료를 자동으로 처리하는 스크립트 예제:

```bash
#!/bin/bash
# check_sso_session.sh

PROFILE="twodragon"

# 세션 확인
if ! aws sts get-caller-identity --profile $PROFILE &>/dev/null; then
    echo "SSO 세션이 만료되었습니다. 다시 로그인합니다..."
    aws sso login --profile $PROFILE
else
    echo "SSO 세션이 유효합니다."
fi
```

## Prowler와 AWS SSO 통합

Prowler는 AWS SSO 프로필을 자동으로 인식합니다:

```bash
# Prowler 실행 시 프로필 지정
prowler aws --profile twodragon

# 또는 환경 변수 사용
export AWS_PROFILE=twodragon
prowler aws
```

## 문제 해결

### 1. "SSO session expired" 오류

```bash
# 해결: 다시 로그인
aws sso login --profile twodragon
```

### 2. "Profile not found" 오류

```bash
# 해결: ~/.aws/config 파일 확인
cat ~/.aws/config

# 프로필이 없으면 추가
aws configure sso --profile twodragon
```

### 3. "Access Denied" 오류

```bash
# 해결: 
# 1. 올바른 역할에 할당되어 있는지 확인
# 2. SSO 관리자에게 권한 요청
# 3. 올바른 계정 ID 확인
```

### 4. Prowler 실행 시 인증 오류

```bash
# 해결: Prowler에 프로필 전달 확인
prowler aws --profile twodragon --region ap-northeast-2

# 또는 환경 변수 설정
export AWS_PROFILE=twodragon
prowler aws
```

## 참고 자료

- [AWS SSO 사용자 가이드](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)
- [AWS CLI SSO 설정](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)
- [Prowler 공식 문서](https://docs.prowler.com)
- [Prowler GitHub](https://github.com/prowler-cloud/prowler)

