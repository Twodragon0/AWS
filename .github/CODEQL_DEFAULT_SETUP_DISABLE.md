# CodeQL Default Setup 비활성화 가이드

## ⚠️ 중요: 현재 문제

CodeQL Default setup이 실행되고 있어서 다음 문제가 발생하고 있습니다:

1. **Python 파싱 오류**: `Bedrock/node_modules/aws-cdk/lib/init-templates/**/*.py` 파일들이 스캔되어 파싱 오류 발생
2. **커스텀 워크플로우와 충돌**: Default setup과 커스텀 워크플로우가 동시에 실행되면 충돌 가능

## 🔧 해결 방법: Default Setup 비활성화

### 단계별 가이드

1. **GitHub 저장소로 이동**
   - 저장소 페이지: `https://github.com/YOUR_USERNAME/aws-devsecops-infrastructure`

2. **Settings 페이지로 이동**
   - 저장소 상단의 **Settings** 탭 클릭
   - 또는 직접 이동: `https://github.com/YOUR_USERNAME/aws-devsecops-infrastructure/settings`

3. **Code security and analysis 섹션 찾기**
   - 왼쪽 사이드바에서 **Code security and analysis** 클릭
   - 또는 직접 이동: `https://github.com/YOUR_USERNAME/aws-devsecops-infrastructure/settings/security_analysis`

4. **Code scanning 섹션 찾기**
   - 페이지에서 **Code scanning** 섹션 찾기
   - **CodeQL analysis** 옆에 **Configure** 또는 **Set up** 버튼이 있을 수 있습니다

5. **Default setup 비활성화**
   - **CodeQL analysis** 옆의 **Disable** 버튼 클릭
   - 확인 메시지에서 **Disable** 확인
   - 또는 **Configure**를 클릭한 후 **Disable** 선택

### 대안: C/C++ 언어만 제거

Default setup을 완전히 비활성화하지 않고 C/C++ 언어만 제거할 수도 있습니다:

1. **CodeQL analysis** 옆의 **Configure** 클릭
2. **Languages** 섹션에서:
   - ✅ **JavaScript / TypeScript** (체크 유지)
   - ✅ **Python** (체크 유지)
   - ❌ **C / C++** (체크 해제)
3. **Save changes** 클릭

## ✅ 확인 사항

Default setup을 비활성화한 후:

1. **Settings** > **Code security and analysis** 페이지로 돌아가기
2. **Code scanning** 섹션에서 **Default setup**이 **Disabled** 상태인지 확인
3. **Actions** 탭에서 커스텀 워크플로우(`.github/workflows/codeql.yml`)가 정상 실행되는지 확인

## 📝 커스텀 워크플로우의 장점

커스텀 워크플로우(`.github/workflows/codeql.yml`)는 다음 기능을 제공합니다:

- ✅ JavaScript와 Python만 스캔 (C/C++ 제외)
- ✅ `node_modules/aws-cdk` 템플릿 파일 자동 제거
- ✅ Python 캐시 파일 제외
- ✅ 더 세밀한 제어 가능
- ✅ Default setup과의 충돌 방지

## 🔍 문제 해결

만약 Default setup을 비활성화한 후에도 문제가 발생하면:

1. **워크플로우 로그 확인**
   - **Actions** 탭 > 실패한 워크플로우 > 로그 확인

2. **파일 정리 단계 확인**
   - 워크플로우의 "Clean up node_modules and aws-cdk templates before CodeQL" 단계가 실행되었는지 확인

3. **CodeQL 설정 확인**
   - `.github/codeql-config.yml` 파일 확인
   - `.github/workflows/codeql.yml` 파일 확인

## 📚 참고 문서

- [CodeQL 문제 해결 가이드](.github/CODEQL_TROUBLESHOOTING.md)
- [CodeQL 이슈 해결 요약](.github/CODEQL_FIX_SUMMARY.md)

