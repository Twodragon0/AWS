# CodeQL 문제 해결 가이드

이 문서는 CodeQL 분석 실패 문제를 해결하기 위한 가이드입니다.

## 🔍 일반적인 오류 및 해결 방법

### 1. "CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled"

**증상**:
```
Error: Code Scanning could not process the submitted SARIF file:
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

**원인**:
- GitHub 저장소에서 CodeQL의 기본 설정(Default setup)이 활성화되어 있음
- 커스텀 CodeQL 워크플로우와 기본 설정이 충돌

**해결 방법**:

1. **GitHub 저장소 설정에서 기본 설정 비활성화**:
   - 저장소로 이동
   - **Settings** > **Code security and analysis** 이동
   - **Code scanning** 섹션 찾기
   - **Default setup**이 활성화되어 있다면 **Disable** 클릭
   - 변경사항 저장

2. **또는 다음 경로로 이동**:
   - **Settings** > **Security** > **Code security and analysis**
   - **Code scanning**에서 기본 설정 비활성화

**참고**: 기본 설정을 비활성화한 후에도 커스텀 워크플로우는 계속 작동합니다.

---

### 2. 타임아웃 오류

**증상**:
- 워크플로우가 5분 또는 33분 후 실패
- "Job timeout" 또는 "Step timeout" 메시지

**원인**:
- 대규모 코드베이스 분석 시간 초과
- 빌드 과정이 너무 오래 걸림

**해결 방법**:

1. **워크플로우에 타임아웃 설정 추가** (이미 적용됨):
   ```yaml
   timeout-minutes: 45
   ```

2. **빌드 단계 최적화**:
   - 불필요한 빌드 단계 제거
   - `continue-on-error: true` 사용하여 빌드 실패 시에도 분석 계속

3. **분석 범위 축소**:
   - 테스트 코드 제외
   - 특정 디렉토리만 분석

---

### 3. 빌드 실패

**증상**:
- npm install 또는 npm build 실패
- Python 패키지 설치 실패

**해결 방법**:

1. **에러 핸들링 개선**:
   ```yaml
   - name: Build
     run: |
       npm ci || echo "Build failed, continuing..."
       npm run build || echo "Build failed, continuing..."
   ```

2. **의존성 확인**:
   - `package.json` 파일 확인
   - `package-lock.json` 파일 존재 확인
   - Python `requirements.txt` 확인

---

### 4. "No supported build system detected" (C/C++ 언어)

**증상**:
```
CodeQL exited with errors
No supported build system detected
CodeQL could not detect the build command.
```

**원인**:
- GitHub 저장소의 CodeQL 기본 설정(Default setup)에서 C/C++ 언어가 자동으로 감지됨
- 이 프로젝트에는 실제 C/C++ 소스 코드가 없고, Python 패키지(numpy, pandas 등) 내부의 C 확장 파일만 존재
- C/C++ 빌드 시스템이 없어서 CodeQL이 빌드 명령을 감지하지 못함

**해결 방법**:

1. **GitHub 저장소 설정에서 C/C++ 언어 제거**:
   - 저장소로 이동: `https://github.com/YOUR_USERNAME/YOUR_REPO`
   - **Settings** > **Code security and analysis** 이동
   - **Code scanning** 섹션에서 **CodeQL analysis** 클릭
   - **Configure** 또는 **Edit** 클릭
   - **Languages** 섹션에서 **C/C++** 언어 제거
   - **JavaScript**와 **Python**만 유지
   - 변경사항 저장

2. **또는 CodeQL 기본 설정 완전히 비활성화**:
   - **Settings** > **Code security and analysis** 이동
   - **Code scanning** 섹션에서 **Default setup** 비활성화
   - 커스텀 워크플로우만 사용 (권장)

**참고**: 이 프로젝트는 JavaScript와 Python만 사용하므로 C/C++ 언어는 필요하지 않습니다.

---

### 5. "Could not process some files due to syntax errors" (Python)

**증상**:
```
Could not process some files due to syntax errors
A parse error occurred while processing .../node_modules/aws-cdk/lib/init-templates/app/python/app.template.py
```

**원인**:
- `node_modules` 내의 AWS CDK 템플릿 파일들이 CodeQL에 의해 스캔됨
- 이러한 템플릿 파일들은 완전한 Python 파일이 아니어서 파싱 오류 발생
- Python 패키지 의존성 내부의 파일들이 스캔됨

**해결 방법**:

1. **워크플로우에서 자동으로 제외됨** (이미 적용됨):
   - `paths-ignore`에 `**/node_modules/**` 및 `**/aws-cdk/**` 추가됨
   - Python 분석 전에 문제가 되는 파일 자동 삭제

2. **수동 확인**:
   ```bash
   # 문제가 되는 파일 확인
   find . -path "*/node_modules/aws-cdk/lib/init-templates/**/*.py" -type f
   
   # 파일 삭제 (워크플로우에서 자동 처리됨)
   find . -path "*/node_modules/aws-cdk/lib/init-templates/**/*.py" -type f -delete
   ```

3. **.gitignore 확인**:
   - `node_modules`가 `.gitignore`에 포함되어 있는지 확인
   - CodeQL은 기본적으로 `.gitignore`를 존중합니다

**참고**: 이러한 경고는 분석 결과에는 영향을 주지 않으며, 실제 프로젝트 코드만 분석됩니다.

---

### 6. 메모리 부족 오류

**증상**:
- "Out of memory" 오류
- 분석이 중간에 실패

**해결 방법**:

1. **더 큰 러너 사용** (GitHub Enterprise에서만 가능):
   ```yaml
   runs-on: ubuntu-latest-4-cores
   ```

2. **분석 범위 축소**:
   - CodeQL 설정에서 특정 경로만 분석

---

## 🔧 워크플로우 최적화 팁

### 1. 병렬 처리

현재 워크플로우는 이미 매트릭스를 사용하여 병렬 처리하고 있습니다:
```yaml
strategy:
  matrix:
    language: [ 'javascript', 'python' ]
```

### 2. 캐싱 활용

Node.js 프로젝트의 경우 npm 캐시를 활용:
```yaml
- uses: actions/setup-node@v4
  with:
    cache: 'npm'
```

### 3. 불필요한 단계 제거

- 테스트 실행 제거 (분석만 수행)
- 문서 생성 단계 제거

---

## 📊 로그 확인 방법

1. **GitHub Actions 페이지로 이동**
2. **실패한 워크플로우 실행 클릭**
3. **실패한 Job 클릭**
4. **실패한 Step의 로그 확인**

주요 확인 사항:
- 초기화 단계의 오류 메시지
- 빌드 단계의 오류 메시지
- 분석 단계의 오류 메시지

---

## 🆘 추가 도움말

### GitHub 공식 문서
- [CodeQL 문제 해결](https://docs.github.com/en/code-security/code-scanning/troubleshooting-code-scanning)
- [CodeQL Action 문서](https://github.com/github/codeql-action)

### 커뮤니티 지원
- [GitHub Community Forum](https://github.community/)
- [GitHub Discussions](https://github.com/github/codeql-action/discussions)

---

## ✅ 체크리스트

문제 해결 전 확인 사항:

- [ ] GitHub 저장소에서 CodeQL 기본 설정이 비활성화되어 있는가?
- [ ] CodeQL 언어 설정에서 JavaScript와 Python만 활성화되어 있는가? (C/C++ 제거)
- [ ] 워크플로우 파일의 문법이 올바른가?
- [ ] 필요한 파일들(package.json, requirements.txt 등)이 존재하는가?
- [ ] 타임아웃 설정이 적절한가?
- [ ] 권한(permissions)이 올바르게 설정되어 있는가?
- [ ] `node_modules`와 `aws-cdk` 템플릿 파일이 제외되어 있는가?

---

**마지막 업데이트**: 2025-01-27

