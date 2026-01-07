# ISMS-P 2025 Prowler 활용 사용 예제

## 기본 사용법

### 1. 전체 평가 실행

```bash
# 환경 변수 설정
export AWS_REGION=ap-northeast-2
export ISMS_OUTPUT_DIR=./output

# 전체 평가 실행 (자산 식별 + 보안 점검 + 위험 평가)
python prowler_isms_2025.py
```

**출력:**
- `isms_risk_report_YYYYMMDD_HHMMSS.json`: 위험 평가 보고서
- `prowler_scan_YYYYMMDD_HHMMSS.json`: Prowler 스캔 결과

### 2. 대시보드 생성

```bash
# 위험 평가 보고서로부터 대시보드 생성
python risk_dashboard.py output/isms_risk_report_20241201_120000.json

# 출력 파일 지정
python risk_dashboard.py output/isms_risk_report_20241201_120000.json -o dashboard.html
```

## 고급 사용법

### 1. 특정 서비스만 점검

```python
from prowler_isms_2025 import ProwlerISMS2025
from utils.config import Config

config = Config.from_env()
assessor = ProwlerISMS2025(config)

# EC2와 S3만 점검
prowler_output = assessor.run_prowler_scan(
    output_format='json',
    services=['ec2', 's3']
)
```

### 2. 컴플라이언스 프레임워크 지정

```python
# CIS 기준 점검
prowler_output = assessor.run_prowler_scan(
    output_format='json',
    compliance_framework='cis'
)

# NIST 기준 점검
prowler_output = assessor.run_prowler_scan(
    output_format='json',
    compliance_framework='nist'
)
```

### 3. 자산 중요도 수동 설정

AWS 태그를 통해 자산 중요도를 설정할 수 있습니다:

```bash
# EC2 인스턴스에 중요도 태그 추가
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=Importance,Value=Critical \
         Key=DataClassification,Value=Restricted \
         Key=Environment,Value=Production
```

태그 옵션:
- `Importance`: Critical, High, Medium, Low
- `DataClassification`: Public, Internal, Confidential, Restricted
- `Environment`: Production, Staging, Test, Development

### 4. 위험 평가 결과 분석

```python
import json
from pathlib import Path

# 보고서 로드
with open('isms_risk_report_20241201_120000.json', 'r') as f:
    report = json.load(f)

# Critical 위험 자산 목록
critical_assets = [
    a for a in report['assessments']
    if a['risk_level'] == 'Critical'
]

print(f"Critical 위험 자산: {len(critical_assets)}개")
for asset in critical_assets:
    print(f"  - {asset['asset_name']}: {asset['risk_score']}점")
```

## CI/CD 통합

### GitHub Actions 예제

```yaml
name: ISMS-P Risk Assessment

on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 오전 9시
  workflow_dispatch:

jobs:
  risk-assessment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r ISMS/requirements.txt
          pip install prowler
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-2
      
      - name: Run risk assessment
        run: |
          cd ISMS/isms-p-cloud-audit
          python prowler_isms_2025.py
      
      - name: Generate dashboard
        run: |
          cd ISMS/isms-p-cloud-audit
          python risk_dashboard.py output/isms_risk_report_*.json
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: risk-reports
          path: ISMS/isms-p-cloud-audit/output/
```

## Lambda 함수로 실행

### Lambda 함수 코드 예제

```python
import json
import os
from prowler_isms_2025 import ProwlerISMS2025
from utils.config import Config

def lambda_handler(event, context):
    """Lambda 함수 핸들러"""
    try:
        # 설정
        config = Config.from_env()
        config.output_dir = '/tmp/output'
        
        # 평가 실행
        assessor = ProwlerISMS2025(config)
        results = assessor.run_full_assessment()
        
        # 결과를 S3에 업로드 (선택적)
        # s3_client = boto3.client('s3')
        # s3_client.upload_file(
        #     str(results['report_file']),
        #     'isms-reports-bucket',
        #     f"reports/{results['report_file'].name}"
        # )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Risk assessment completed',
                'summary': results['summary']
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
```

### EventBridge 스케줄 설정

```json
{
  "Rules": [
    {
      "Name": "isms-weekly-risk-assessment",
      "ScheduleExpression": "cron(0 9 ? * MON *)",
      "State": "ENABLED",
      "Targets": [
        {
          "Arn": "arn:aws:lambda:ap-northeast-2:123456789012:function:isms-risk-assessment",
          "Id": "1"
        }
      ]
    }
  ]
}
```

## 알림 설정

### Slack 알림 예제

```python
import requests
import json
from pathlib import Path

def send_slack_notification(report_file: Path, webhook_url: str):
    """Slack으로 위험 평가 결과 알림 전송"""
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    summary = report['summary']
    
    message = {
        "text": "ISMS-P 2025 위험 평가 완료",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "ISMS-P 2025 위험 평가 결과"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Critical 위험:* {summary['critical_risks']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*High 위험:* {summary['high_risks']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*평균 위험 점수:* {summary['average_risk_score']}"
                    }
                ]
            }
        ]
    }
    
    response = requests.post(webhook_url, json=message)
    return response.status_code == 200
```

## 모니터링 및 추적

### 위험 추이 분석

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_risk_trends(reports_dir: Path, days: int = 30):
    """지난 N일간의 위험 추이 분석"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    reports = []
    for report_file in reports_dir.glob('isms_risk_report_*.json'):
        report_time = datetime.strptime(
            report_file.stem.split('_')[-2] + '_' + report_file.stem.split('_')[-1],
            '%Y%m%d_%H%M%S'
        )
        
        if start_date <= report_time <= end_date:
            with open(report_file, 'r') as f:
                report = json.load(f)
                reports.append({
                    'date': report_time,
                    'summary': report['summary']
                })
    
    # 날짜순 정렬
    reports.sort(key=lambda x: x['date'])
    
    # 추이 분석
    for report in reports:
        print(f"{report['date'].strftime('%Y-%m-%d')}: "
              f"Critical={report['summary']['critical_risks']}, "
              f"Average Score={report['summary']['average_risk_score']}")
```

## 문제 해결

### Prowler 실행 시간이 오래 걸리는 경우

```python
# 특정 서비스만 점검하여 시간 단축
prowler_output = assessor.run_prowler_scan(
    output_format='json',
    services=['ec2', 's3', 'iam']  # 필요한 서비스만 지정
)
```

### 메모리 부족 오류

```python
# 배치 처리로 분할 실행
services_batches = [
    ['ec2', 's3'],
    ['rds', 'lambda'],
    ['iam', 'cloudfront']
]

for batch in services_batches:
    prowler_output = assessor.run_prowler_scan(
        output_format='json',
        services=batch
    )
```

## 참고 자료

- [Prowler 공식 문서](https://docs.prowler.com)
- [ISMS-P 인증 가이드](https://isms.go.kr)
- [AWS 보안 모범 사례](https://aws.amazon.com/security/best-practices/)

