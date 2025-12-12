# Secret Scanning 가이드

## 개요

이 리포지토리는 public repository이므로 민감한 정보가 노출되지 않도록 주의해야 합니다.

## 금지 사항

다음과 같은 정보는 **절대** 리포지토리에 커밋하면 안 됩니다:

### API 키 및 토큰
- Slack 토큰 (`xoxb-`, `xoxp-`, `xoxa-`, `xoxr-`, `xoxo-`)
- GitHub Personal Access Tokens (`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`)
- AWS Access Keys (`AKIA...`)
- AWS Session Tokens
- Google API Keys (`AIza...`)
- Stripe API Keys (`sk_live_`, `sk_test_`, `pk_live_`, `pk_test_`)

### 비밀번호 및 인증 정보
- 데이터베이스 비밀번호
- 서비스 계정 비밀번호
- 암호화 키
- 개인 키 파일 (`.pem`, `.key`, `.p12`, `.pfx`)

### 기타 민감한 정보
- Terraform state 파일 (`*.tfstate`, `*.tfstate.backup`)
- CDK 빌드 아티팩트 (`cdk.out/`)
- 환경 변수 파일 (`.env`, `.env.local`)
- AWS 자격 증명 파일 (`~/.aws/credentials`)

## 안전한 방법

### 1. AWS Secrets Manager 사용
```typescript
// ❌ 나쁜 예: 하드코딩된 토큰
const token = "hardcoded-token-value"; // 절대 이렇게 하지 마세요!

// ✅ 좋은 예: Secrets Manager에서 가져오기
const token = secretsmanager.Secret.fromSecretNameV2(
  this, 'SlackToken', '/slack/bot-token'
).secretValue.unsafeUnwrap();
```

### 2. 환경 변수 사용
```bash
# .env 파일 (Git에 커밋하지 않음)
# 실제 값은 환경 변수로 설정
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
```

### 3. CDK Context 사용
```bash
cdk deploy --context slackBotToken=xxx --context slackSigningSecret=yyy
```

### 4. Terraform 변수 사용
```hcl
variable "api_key" {
  description = "API Key"
  type        = string
  sensitive   = true
}
```

## 사전 검사

커밋 전에 다음 명령어로 검사하세요:

```bash
# 민감한 패턴 검색 (예시 패턴만 검색, 실제 토큰은 포함하지 않음)
grep -rE "(xox[baprs]-|AKIA|ghp_|sk_live_)" --include="*.ts" --include="*.js" --include="*.py" .

# Git에 추적되지 않은 파일 확인
git status

# .gitignore 확인
cat .gitignore
```

## 문제 발견 시

1. **즉시 토큰/키 무효화**
2. **Git에서 파일 제거**: `git rm --cached <file>`
3. **커밋 및 푸시**: 변경사항을 즉시 푸시
4. **Git 히스토리 정리** (선택사항):
   ```bash
   # BFG Repo-Cleaner 사용 (권장)
   bfg --replace-text passwords.txt
   
   # 또는 git filter-branch 사용
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch <file>" \
     --prune-empty --tag-name-filter cat -- --all
   ```

## 자동화

GitHub의 Secret Scanning 기능이 활성화되어 있으면 자동으로 감지됩니다.

CI/CD 파이프라인에서도 검사:
```yaml
- name: Secret Scanning
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
```

## 참고 자료

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_cryptographic_key)

