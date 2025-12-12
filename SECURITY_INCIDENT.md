# 보안 사고 보고서

## 발견된 문제

### 1. 하드코딩된 Slack 토큰 및 비밀번호 (심각)

**위치:**
- `Bedrock/cdk.out/AmazonBedrockKnowledgebaseSlackbotStack.template.json`
- `Bedrock/cdk.out/tree.json`

**노출된 정보:**
- Slack Bot Token: `xoxb-3185905655123-8701509597540-yfx5WYyrBHNLIkg7Z52WZ06M`
- Slack Signing Secret: `a1a344a28870c308b2a218bdc810da3d`

**조치 사항:**
1. ✅ Git에서 `cdk.out` 디렉토리 제거
2. ✅ `.gitignore`에 `cdk.out/` 추가
3. ⚠️ **즉시 조치 필요**: Slack 앱에서 해당 토큰을 무효화하고 새 토큰을 발급받아야 합니다.

### 2. Terraform State 파일 노출

**위치:**
- `Cloudfront/s3-cloudfront-cdn/terraform.tfstate`
- `EC2/terraform/initial_setup/terraform.tfstate`
- 기타 여러 `terraform.tfstate` 파일들

**조치 사항:**
1. ✅ Git에서 모든 `terraform.tfstate*` 파일 제거
2. ✅ `.gitignore`에 `*.tfstate*` 추가

## 권장 사항

### 즉시 조치
1. **Slack 토큰 무효화**: 
   - https://api.slack.com/apps 에서 해당 앱의 토큰을 즉시 무효화
   - 새 토큰 발급 후 AWS Secrets Manager에 저장

2. **Git 히스토리 정리** (선택사항):
   ```bash
   # BFG Repo-Cleaner 사용 (권장)
   # 또는 git filter-branch 사용
   ```

3. **민감한 정보 검색**:
   - GitHub의 Secret Scanning 기능 활성화
   - 정기적인 보안 스캔 수행

### 예방 조치
1. ✅ `.gitignore`에 빌드 아티팩트 추가
2. ✅ Pre-commit hook으로 민감한 정보 검사
3. ✅ CI/CD 파이프라인에서 보안 스캔 자동화
4. ✅ Secrets Manager 또는 환경 변수 사용

## 참고
- 이 문서는 보안 사고 대응을 위한 것입니다.
- 모든 민감한 정보는 AWS Secrets Manager 또는 환경 변수를 통해 관리해야 합니다.

