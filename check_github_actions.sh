#!/bin/bash
# GitHub Actions 워크플로우 상태 확인 스크립트

set -e

REPO="Twodragon0/AWS"
echo "=========================================="
echo "GitHub Actions 워크플로우 상태 확인"
echo "Repository: $REPO"
echo "=========================================="
echo ""

# 최신 워크플로우 실행 목록
echo "📊 최신 워크플로우 실행 상태:"
echo "----------------------------------------"
gh run list --limit 10 --json name,status,conclusion,createdAt,headBranch,workflowName --jq '.[] | "\(.workflowName) | \(.status) | \(.conclusion // "N/A") | \(.createdAt)"' | column -t -s '|'
echo ""

# 각 워크플로우별 최신 상태
echo "📋 워크플로우별 최신 상태:"
echo "----------------------------------------"

WORKFLOWS=("codeql.yml" "security-scan.yml" "terraform-security-scan.yml" "secret-scanning.yml")

for workflow in "${WORKFLOWS[@]}"; do
    echo ""
    echo "🔍 $workflow:"
    LATEST=$(gh run list --workflow="$workflow" --limit 1 --json databaseId,status,conclusion,createdAt,displayTitle 2>/dev/null || echo "[]")
    if [ "$LATEST" != "[]" ] && [ -n "$LATEST" ]; then
        echo "$LATEST" | jq -r '.[] | "  Status: \(.status)\n  Conclusion: \(.conclusion // "N/A")\n  Created: \(.createdAt)\n  Title: \(.displayTitle)"'
        
        # 실패한 경우 상세 정보 표시
        CONCLUSION=$(echo "$LATEST" | jq -r '.[0].conclusion // ""')
        if [ "$CONCLUSION" = "failure" ]; then
            RUN_ID=$(echo "$LATEST" | jq -r '.[0].databaseId')
            echo "  ⚠️  실패한 Job 정보:"
            gh run view $RUN_ID --json jobs --jq '.jobs[] | select(.conclusion == "failure") | "    - \(.name): \(.conclusion)"' 2>/dev/null || echo "    (상세 정보를 가져올 수 없습니다)"
        fi
    else
        echo "  워크플로우를 찾을 수 없습니다."
    fi
done

echo ""
echo "=========================================="
echo "✅ 확인 완료"
echo "=========================================="

