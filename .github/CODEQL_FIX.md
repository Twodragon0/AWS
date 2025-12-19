# CodeQL 오류 해결 방법

## 문제
다음 오류가 발생하는 경우:
```
Error: Code Scanning could not process the submitted SARIF file:
CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled
```

또는 워크플로우가 타임아웃되거나 실패하는 경우

## 빠른 해결 방법

### ⚠️ 필수: GitHub 저장소 설정 변경

**상세한 단계별 가이드는 [CODEQL_SETUP_INSTRUCTIONS.md](./CODEQL_SETUP_INSTRUCTIONS.md)를 참조하세요.**

간단 요약:
1. GitHub 저장소로 이동
2. **Settings** > **Code security and analysis** 이동
3. **Code scanning** 섹션에서 **Default setup** 비활성화
4. 변경사항 저장

### 워크플로우 개선 사항

다음 개선 사항이 이미 적용되었습니다:
- ✅ 타임아웃 설정 추가 (45분)
- ✅ 에러 핸들링 개선
- ✅ 빌드 단계 최적화
- ✅ 명시적인 upload 설정

## 추가 문제 해결

자세한 문제 해결 가이드는 [CODEQL_TROUBLESHOOTING.md](./CODEQL_TROUBLESHOOTING.md)를 참조하세요.

## 참고
- 이 워크플로우는 커스텀 CodeQL 설정을 사용하므로 GitHub의 기본 설정과 충돌할 수 있습니다
- 기본 설정을 비활성화한 후 워크플로우가 정상적으로 작동합니다
- 워크플로우는 이미 최적화되어 있으며, 저장소 설정만 변경하면 됩니다

