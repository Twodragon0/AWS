# CodeQL 설정 완료 가이드

## ⚠️ 중요: GitHub 저장소 설정 변경 필요

CodeQL 분석이 실패하는 주요 원인은 GitHub 저장소에서 CodeQL의 기본 설정(Default setup)이 활성화되어 있기 때문입니다.

## 🔧 해결 단계

### 1단계: GitHub 저장소 설정 확인

1. GitHub 저장소로 이동: `https://github.com/YOUR_USERNAME/YOUR_REPO`
2. **Settings** 탭 클릭
3. 왼쪽 사이드바에서 **Code security and analysis** 클릭
   - 또는 직접 이동: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/security_analysis`

### 2단계: CodeQL 기본 설정 비활성화

**방법 A: Code security and analysis 페이지에서**

1. **Code scanning** 섹션 찾기
2. **CodeQL analysis** 또는 **Set up code scanning** 옵션 확인
3. **Default setup**이 **Enabled**로 표시되어 있다면:
   - **Configure** 또는 **Set up** 버튼 클릭
   - **Disable** 또는 **Remove** 클릭
   - 확인 메시지에서 **Disable** 확인

**방법 B: Security 탭에서**

1. 저장소의 **Security** 탭 클릭
2. **Code scanning** 섹션 찾기
3. 설정 아이콘(⚙️) 클릭
4. **Disable** 선택

### 3단계: 변경사항 확인

1. **Settings** > **Code security and analysis** 페이지로 돌아가기
2. **Code scanning** 섹션에서 **Default setup**이 비활성화되었는지 확인
3. 상태가 **Disabled** 또는 설정이 없어야 함

### 4단계: 워크플로우 재실행

1. **Actions** 탭으로 이동
2. 실패한 워크플로우 실행 찾기
3. **Re-run jobs** 클릭하여 재실행
4. 또는 새로운 커밋을 푸시하여 자동 실행

## 📸 스크린샷 가이드

### Code security and analysis 페이지 위치

```
Repository Settings
├── General
├── Access
├── Secrets and variables
├── Actions
├── Code security and analysis  ← 여기!
├── ...
```

### Code scanning 섹션 예시

```
Code scanning
├── CodeQL analysis
│   ├── Default setup: Enabled  ← 이것을 Disabled로 변경
│   └── [Configure] 버튼
└── ...
```

## ✅ 확인 체크리스트

설정 완료 후 확인:

- [ ] Code scanning의 Default setup이 비활성화됨
- [ ] 커스텀 CodeQL 워크플로우가 정상 작동함
- [ ] Actions에서 CodeQL 분석이 성공함

## 🚨 여전히 실패하는 경우

### 추가 확인 사항

1. **권한 확인**:
   - 저장소 관리자 권한이 있는지 확인
   - Organization 저장소인 경우 관리자 승인 필요할 수 있음

2. **워크플로우 파일 확인**:
   - `.github/workflows/codeql.yml` 파일이 올바른지 확인
   - YAML 문법 오류가 없는지 확인

3. **로그 확인**:
   - Actions 탭에서 실패한 워크플로우의 로그 확인
   - 구체적인 오류 메시지 확인

### 추가 도움말

- [CodeQL 문제 해결 가이드](./CODEQL_TROUBLESHOOTING.md)
- [GitHub CodeQL 문서](https://docs.github.com/en/code-security/code-scanning)

## 📝 참고 사항

- 기본 설정을 비활성화해도 커스텀 워크플로우는 계속 작동합니다
- 기본 설정과 커스텀 워크플로우를 동시에 사용할 수 없습니다
- 커스텀 워크플로우가 더 유연하고 제어 가능합니다

---

**마지막 업데이트**: 2025-01-27

