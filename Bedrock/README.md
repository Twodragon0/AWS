# Amazon Bedrock Knowledge Base Slack Bot

> Amazon Bedrock Knowledge Base를 활용한 Slack 챗봇

이 프로젝트는 Amazon Bedrock Knowledge Base와 Slack을 통합하여 RAG(Retrieval-Augmented Generation) 기반 AI 챗봇을 구축합니다. AWS Well-Architected Framework 문서를 Knowledge Base로 활용하여 AWS 아키텍처 및 보안 모범 사례에 대한 질문에 답변합니다.

**참고**: 이 프로젝트는 [GitHub 저장소](https://github.com/Twodragon0/amazon-bedrock-knowledgebase-slackbot)와 [블로그 포스트](https://twodragon.tistory.com/673)를 기반으로 합니다.

## 📋 목차

- [개요](#개요)
- [아키텍처](#아키텍처)
- [주요 기능](#주요-기능)
- [사전 요구 사항](#사전-요구-사항)
- [배포 방법](#배포-방법)
- [사용 방법](#사용-방법)
- [보안 고려사항](#보안-고려사항)
- [강의 연계](#강의-연계)

## 🎯 개요

Amazon Bedrock Knowledge Base는 RAG(Retrieval-Augmented Generation) 기능을 제공하여 대규모 문서 세트에서 정확한 답변을 생성할 수 있습니다. 이 프로젝트는 다음과 같은 기능을 제공합니다:

- **Slack 통합**: Slack Bolt for Python을 사용한 Slack 앱 통합
- **Knowledge Base**: AWS Well-Architected Framework 문서를 Knowledge Base로 활용
- **OpenSearch Serverless**: 벡터 데이터베이스로 OpenSearch Serverless 사용
- **Lambda 기반**: 서버리스 아키텍처로 Lambda 함수 사용

### 사용 사례

- AWS 아키텍처 모범 사례 질문
- 보안 가이드라인 조회
- 운영 우수 사례 확인
- 비용 최적화 전략 문의

## 🏗️ 아키텍처

### 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Slack"
        SlackUser[Slack 사용자]
        SlackApp[Slack App]
    end
    
    subgraph "AWS API Gateway"
        APIGateway[API Gateway<br/>REST API]
    end
    
    subgraph "Lambda Functions"
        RequestProcessor[Request Processor Lambda<br/>Slack Bolt]
        CreateIndex[Create Index Lambda<br/>Knowledge Base 초기화]
    end
    
    subgraph "Amazon Bedrock"
        BedrockKB[Bedrock Knowledge Base]
        BedrockModel[Bedrock Foundation Model<br/>Claude, Titan 등]
    end
    
    subgraph "Vector Database"
        OpenSearch[OpenSearch Serverless<br/>AOSS]
        Index[AOSS Index]
    end
    
    subgraph "Storage"
        S3[S3 Bucket<br/>문서 저장]
    end
    
    subgraph "Security"
        SecretsManager[Secrets Manager<br/>Slack Signing Secret]
        KMS[KMS<br/>암호화]
    end
    
    SlackUser -->|슬래시 명령어| SlackApp
    SlackApp -->|HTTP POST| APIGateway
    APIGateway --> RequestProcessor
    RequestProcessor --> SecretsManager
    RequestProcessor --> BedrockKB
    BedrockKB --> OpenSearch
    OpenSearch --> Index
    BedrockKB --> BedrockModel
    BedrockKB --> S3
    CreateIndex --> OpenSearch
    CreateIndex --> S3
    
    RequestProcessor -.->|암호화| KMS
    BedrockKB -.->|암호화| KMS
    
    style SlackApp fill:#4A154B
    style BedrockKB fill:#232F3E
    style OpenSearch fill:#005571
    style RequestProcessor fill:#FF9900
```

### RAG 프로세스 흐름

```mermaid
sequenceDiagram
    participant User as Slack 사용자
    participant Slack as Slack App
    participant API as API Gateway
    participant Lambda as Request Processor
    participant KB as Bedrock KB
    participant AOSS as OpenSearch
    participant Model as Bedrock Model
    
    User->>Slack: /ask-aws 질문 입력
    Slack->>API: HTTP POST 요청
    API->>Lambda: 이벤트 전달
    Lambda->>Lambda: Slack 서명 검증
    Lambda->>KB: 질문 전달
    KB->>AOSS: 벡터 검색
    AOSS-->>KB: 관련 문서 반환
    KB->>Model: 컨텍스트 + 질문
    Model-->>KB: 답변 생성
    KB-->>Lambda: 최종 답변
    Lambda-->>API: JSON 응답
    API-->>Slack: 메시지 전송
    Slack-->>User: 답변 표시
```

### Python 코드로 본 Bedrock 구조

```python
"""
Amazon Bedrock Knowledge Base Slack Bot 구조
"""
import boto3
import json
import os
from typing import Dict, Optional
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

class BedrockKnowledgeBase:
    """Bedrock Knowledge Base 클래스"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
        self.knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
        self.model_id = os.environ.get('MODEL_ID', 'anthropic.claude-v2')
    
    def retrieve_and_generate(
        self,
        query: str,
        retrieval_config: Optional[Dict] = None
    ) -> Dict:
        """RAG: 검색 및 생성"""
        # Knowledge Base 검색
        retrieval_config = retrieval_config or {
            'vectorSearchConfiguration': {
                'numberOfResults': 5,
                'overrideSearchType': 'HYBRID'
            }
        }
        
        # Retrieve API 호출
        retrieve_response = self.bedrock_agent.retrieve(
            knowledgeBaseId=self.knowledge_base_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration=retrieval_config
        )
        
        # 검색된 문서 추출
        retrieved_documents = retrieve_response.get('retrievalResults', [])
        
        # 컨텍스트 구성
        context = self._build_context(retrieved_documents)
        
        # 생성 프롬프트 구성
        prompt = self._build_prompt(query, context)
        
        # Bedrock 모델 호출
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1024,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']
        
        return {
            'answer': answer,
            'sources': [doc.get('location', {}) for doc in retrieved_documents]
        }
    
    def _build_context(self, documents: list) -> str:
        """검색된 문서로 컨텍스트 구성"""
        context_parts = []
        for doc in documents:
            content = doc.get('content', {}).get('text', '')
            score = doc.get('score', 0)
            context_parts.append(f"[Relevance: {score:.2f}]\n{content}")
        return "\n\n---\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """프롬프트 구성"""
        return f"""You are an AWS architecture expert assistant. Answer the question based on the provided context from AWS Well-Architected Framework documentation.

Context:
{context}

Question: {query}

Instructions:
- Provide accurate and helpful answers based on the context
- If the answer is not in the context, say so
- Include relevant AWS best practices
- Format your response in a clear and readable way

Answer:"""

class SlackBotHandler:
    """Slack Bot 핸들러"""
    
    def __init__(self):
        self.app = App(
            token=os.environ.get('SLACK_BOT_TOKEN'),
            signing_secret=self._get_signing_secret()
        )
        self.bedrock_kb = BedrockKnowledgeBase()
        self._setup_commands()
    
    def _get_signing_secret(self) -> str:
        """Secrets Manager에서 Signing Secret 가져오기"""
        secrets_client = boto3.client('secretsmanager')
        secret_name = os.environ.get('SLACK_SIGNING_SECRET_NAME')
        
        try:
            response = secrets_client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except Exception as e:
            print(f"Error retrieving secret: {e}")
            raise
    
    def _setup_commands(self):
        """Slack 명령어 설정"""
        @self.app.command("/ask-aws")
        def handle_ask_aws(ack, respond, command):
            """/ask-aws 슬래시 명령어 처리"""
            ack()
            
            query = command.get('text', '')
            if not query:
                respond("Please provide a question. Usage: /ask-aws <your question>")
                return
            
            try:
                # Bedrock Knowledge Base에서 답변 검색
                result = self.bedrock_kb.retrieve_and_generate(query)
                
                # Slack 메시지 포맷팅
                message = self._format_response(result['answer'], result['sources'])
                respond(message)
            except Exception as e:
                respond(f"Error: {str(e)}")
    
    def _format_response(self, answer: str, sources: list) -> str:
        """응답 포맷팅"""
        message = f"*Answer:*\n{answer}\n\n"
        
        if sources:
            message += "*Sources:*\n"
            for i, source in enumerate(sources[:3], 1):  # 상위 3개만 표시
                s3_uri = source.get('s3Location', {}).get('uri', 'N/A')
                message += f"{i}. {s3_uri}\n"
        
        return message
    
    def get_handler(self):
        """Lambda 핸들러 반환"""
        handler = SlackRequestHandler(app=self.app)
        return handler

# Lambda 핸들러
def lambda_handler(event, context):
    """Lambda 진입점"""
    bot_handler = SlackBotHandler()
    handler = bot_handler.get_handler()
    return handler.handle(event, context)

# Knowledge Base 초기화 Lambda
def create_index_handler(event, context):
    """Knowledge Base 인덱스 생성"""
    bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
    
    # S3에서 문서 동기화
    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=knowledge_base_id,
        dataSourceId=os.environ.get('DATA_SOURCE_ID')
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'ingestionJobId': response['ingestionJobId'],
            'status': 'STARTED'
        })
    }
```

## 🚀 주요 기능

### 1. RAG (Retrieval-Augmented Generation)
- 벡터 검색을 통한 관련 문서 검색
- 검색된 문서를 컨텍스트로 활용한 정확한 답변 생성
- 하이브리드 검색 (키워드 + 벡터)

### 2. Slack 통합
- 슬래시 명령어 `/ask-aws` 지원
- Slack Bolt for Python 사용
- 서명 검증을 통한 보안 강화

### 3. Knowledge Base 관리
- AWS Well-Architected Framework 문서 자동 인덱싱
- S3 기반 문서 저장
- OpenSearch Serverless 벡터 데이터베이스

### 4. 서버리스 아키텍처
- Lambda 함수 기반
- API Gateway를 통한 HTTP 엔드포인트
- 자동 스케일링

## 📋 사전 요구 사항

### 필수 도구
- **Node.js**: 버전 18 이상
- **npm**: Node.js와 함께 설치
- **AWS CDK**: `npm install -g aws-cdk`로 설치
- **Python**: 버전 3.9 이상
- **AWS CLI**: v2 이상 설치 및 구성

### AWS 서비스 요구사항
- **Bedrock 모델 접근**: Claude 또는 Titan 모델 접근 권한
- **OpenSearch Serverless**: 벡터 데이터베이스 생성 권한
- **S3**: 문서 저장 버킷
- **Secrets Manager**: Slack Signing Secret 저장

### Slack 앱 설정
1. [Slack API](https://api.slack.com/apps)에서 새 앱 생성
2. Slash Commands 추가 (`/ask-aws`)
3. Signing Secret 복사
4. OAuth 토큰 생성

## 🚀 배포 방법

### 1. 저장소 클론

```bash
git clone https://github.com/Twodragon0/amazon-bedrock-knowledgebase-slackbot.git
cd Bedrock
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env << EOF
KNOWLEDGE_BASE_ID=your-knowledge-base-id
MODEL_ID=anthropic.claude-v2
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET_NAME=slack-signing-secret
DATA_SOURCE_ID=your-data-source-id
EOF
```

### 3. CDK 배포

```bash
# 의존성 설치
npm install

# CDK 부트스트랩 (최초 1회)
npx cdk bootstrap

# 배포
npm run build
cdk deploy --all
```

### 4. Knowledge Base 초기화

```bash
# Knowledge Base에 문서 로드
./scripts/load-kb.sh
```

## 💻 사용 방법

### 1. Slack에서 사용

```
/ask-aws What are the security best practices for VPC?
```

### 2. 응답 예시

```
Answer:
Based on AWS Well-Architected Framework, VPC security best practices include:
- Use security groups with least privilege
- Implement network ACLs for additional layer
- Enable VPC Flow Logs for monitoring
- Use VPC Endpoints for private AWS service access

Sources:
1. s3://well-architected-framework/security-pillar/vpc-security.md
2. s3://well-architected-framework/operational-excellence/vpc-monitoring.md
```

### 3. API 직접 호출

```bash
curl -X POST https://your-api-gateway-url/slack/events \
  -H "Content-Type: application/json" \
  -d '{
    "command": "/ask-aws",
    "text": "What is the Well-Architected Framework?",
    "response_url": "https://hooks.slack.com/commands/..."
  }'
```

## 🛡️ DevSecOps 보안 강화

이 프로젝트는 DevSecOps 모범 사례를 적용하여 보안성을 강화했습니다.

### 1. 암호화 및 키 관리

- **KMS 암호화**: 모든 민감한 데이터는 KMS 키로 암호화
  - S3 버킷: KMS 암호화 활성화
  - DynamoDB: 고객 관리형 KMS 키 사용
  - Lambda 환경 변수: KMS 암호화
- **키 로테이션**: KMS 키 자동 로테이션 활성화
- **Secrets Manager**: Slack 토큰 및 시크릿은 Secrets Manager에 저장

### 2. 접근 제어 및 IAM

- **최소 권한 원칙**: 모든 IAM 역할은 필요한 권한만 부여
- **리소스 기반 정책**: 특정 리소스에만 접근 가능하도록 제한
- **조건부 정책**: 계정 ID 기반 조건 추가

### 3. 모니터링 및 감사

- **CloudTrail**: 모든 API 호출 로깅
- **Guardrails**: Bedrock Guardrails를 통한 콘텐츠 필터링
  - 부적절한 콘텐츠 차단 (SEXUAL, VIOLENCE, HATE, INSULTS, MISCONDUCT)
  - 프롬프트 공격 방지 (PROMPT_ATTACK)
  - PII 데이터 익명화/차단
- **입력 검증**: Lambda 함수에서 사용자 입력 검증 및 위험 패턴 감지

### 4. 네트워크 보안

- **VPC 엔드포인트**: 프라이빗 연결을 통한 데이터 전송 (향후 구현 가능)
- **SSL/TLS**: 모든 통신은 HTTPS 강제
- **보안 그룹**: 최소 권한 원칙 적용

### 5. 데이터 보안

- **S3 버킷**: 공개 접근 차단, 버전 관리 활성화
- **OpenSearch Serverless**: 암호화 활성화
- **DynamoDB**: 암호화 및 TTL 설정

## 💰 FinOps 비용 최적화

이 프로젝트는 FinOps 모범 사례를 적용하여 비용을 최적화했습니다.

### 1. 리소스 태깅

모든 리소스에 다음 태그가 적용되어 비용 추적이 가능합니다:
- `Project`: Bedrock-SlackBot
- `Environment`: Production
- `CostCenter`: DevSecOps
- `Owner`: DevSecOps-Team
- `Purpose`: AIOps-Chatbot

### 2. Lambda 비용 최적화

- **메모리 최적화**: 512MB → 256MB로 조정 (필요시 조정 가능)
- **타임아웃 최적화**: 10분 → 5분으로 조정
- **로깅 최적화**: DEBUG → INFO 레벨로 변경하여 로그 비용 절감
- **프로비저닝된 동시성**: 필요시 설정 가능

### 3. S3 비용 최적화

- **Lifecycle 정책**:
  - 30일 후: Standard-IA로 전환
  - 90일 후: Glacier로 전환
  - 365일 후: 이전 버전 자동 삭제
- **Intelligent-Tiering**: 접근 패턴에 따른 자동 스토리지 클래스 이동

### 4. 모니터링 및 알람

- **CloudWatch 비용 알람**: API Gateway 요청 수 기반 알람
- **Budget 설정**: 월 예산 알람 (80%, 100% 임계값)
- **비용 이상 탐지**: Cost Anomaly Detection (선택적)

### 5. Bedrock 모델 비용 최적화

- **모델 선택**: 비용 효율적인 모델 선택 (Claude 3.5 Sonnet)
- **토큰 제한**: max_tokens 설정으로 비용 제어
- **사용량 모니터링**: CloudWatch 메트릭을 통한 모델 사용량 추적

### 6. 비용 모니터링 대시보드

CloudWatch 대시보드에서 다음 메트릭을 모니터링할 수 있습니다:
- Lambda Invocations
- Lambda Errors
- Lambda Duration
- Lambda Throttles
- Bedrock Invocations
- Bedrock Duration
- API Gateway Requests

## 🚀 DevOps 운영 최적화

이 프로젝트는 DevOps 모범 사례를 적용하여 운영 효율성을 향상시켰습니다.

### 1. 모니터링 및 알람

- **CloudWatch 대시보드**: 실시간 메트릭 모니터링
- **알람 설정**:
  - Lambda 에러 알람 (임계값: 5회)
  - Lambda 지속 시간 알람 (임계값: 5분)
  - Lambda 쓰로틀 알람
  - API Gateway 비용 알람
- **SNS 알림**: 알람 발생 시 SNS 토픽을 통한 알림

### 2. 로깅

- **CloudWatch Logs**: 모든 Lambda 함수 로그 수집
- **API Gateway 로깅**: 액세스 로그 및 실행 로그 활성화
- **로그 보관**: 1주일 ~ 1개월 (리소스별 상이)
- **로그 최적화**: 불필요한 로그 최소화로 비용 절감

### 3. 메트릭 수집

Lambda 함수에서 다음 커스텀 메트릭을 발행합니다:
- `CommandRequests`: 슬래시 명령어 요청 수
- `CommandSuccess`: 성공한 요청 수
- `CommandErrors`: 에러 발생 수
- `CommandDuration`: 요청 처리 시간
- `BedrockInvocations`: Bedrock API 호출 수
- `BedrockDuration`: Bedrock 응답 시간
- `BedrockErrors`: Bedrock 에러 수
- `InvalidInput`: 유효하지 않은 입력 수

### 4. 자동화

- **CDK 배포**: Infrastructure as Code를 통한 자동 배포
- **CI/CD**: GitHub Actions를 통한 자동 테스트 및 배포 (선택적)
- **리소스 태깅**: 자동 태깅으로 비용 추적 및 관리

### 5. 에러 처리 및 복원력

- **중복 이벤트 방지**: DynamoDB를 통한 이벤트 추적
- **에러 핸들링**: 모든 예외 상황에 대한 적절한 처리
- **타임아웃 관리**: 적절한 타임아웃 설정으로 무한 대기 방지

### 6. 성능 최적화

- **비동기 처리**: Slack Bolt의 lazy loading 활용
- **캐싱**: 필요시 응답 캐싱으로 비용 절감
- **연결 풀링**: Boto3 클라이언트 재사용

## 🔒 보안 고려사항

### 1. Secrets 관리

```mermaid
graph LR
    A[Slack Signing Secret] --> B[Secrets Manager]
    B --> C[Lambda 환경 변수]
    C --> D[KMS 암호화]
    
    E[Slack Bot Token] --> B
    
    style B fill:#e1f5ff
    style D fill:#fff4e1
```

- Secrets Manager를 통한 시크릿 저장
- KMS를 통한 암호화
- IAM 역할을 통한 최소 권한 접근

### 2. API 보안

- Slack 서명 검증 필수
- API Gateway 인증 및 권한 부여
- VPC 엔드포인트를 통한 프라이빗 연결

### 3. 데이터 보안

- OpenSearch Serverless 암호화
- S3 버킷 암호화
- CloudTrail을 통한 API 로깅

## 📚 강의 연계

이 프로젝트는 [Twodragon의 클라우드 시큐리티 강의](https://twodragon.tistory.com/category/*%20Twodragon/보안%20강의%20%28Course%29)와 연계되어 있으며, 상세한 구현 가이드는 [블로그 포스트](https://twodragon.tistory.com/673)에서 확인할 수 있습니다.

### 블로그 포스트 내용

[Amazon Bedrock Knowledge Base를 활용한 Slack 챗봇 구축](https://twodragon.tistory.com/673) 블로그에서는 다음을 다룹니다:

- Bedrock Knowledge Base 설정
- OpenSearch Serverless 구성
- Slack 앱 통합
- Lambda 함수 구현
- 배포 및 테스트

### 강의 연계

- **AI 보안**: Bedrock 모델 접근 제어
- **서버리스 보안**: Lambda 함수 보안 모범 사례
- **데이터 보안**: 벡터 데이터베이스 암호화
- **API 보안**: API Gateway 및 Slack 통합 보안

## 🐛 문제 해결

### 1. "Invalid Signature" 오류

**증상**: Slack에서 서명 검증 실패

**해결 방법**:
- Secrets Manager의 Signing Secret 확인
- Lambda 환경 변수 확인
- Slack 앱 설정에서 Signing Secret 재확인

### 2. "Knowledge Base Not Found" 오류

**증상**: Lambda에서 Knowledge Base를 찾을 수 없음

**해결 방법**:
- Knowledge Base ID 확인
- IAM 역할 권한 확인
- Bedrock 서비스 활성화 확인

### 3. "Access Denied" 오류

**증상**: Bedrock 또는 OpenSearch 접근 거부

**해결 방법**:
- IAM 역할 권한 확인
- Bedrock 모델 접근 권한 확인
- OpenSearch Serverless 접근 정책 확인

### 4. 응답 지연

**증상**: 챗봇 응답이 느림

**해결 방법**:
- Lambda 메모리 크기 증가
- OpenSearch Serverless 성능 확인
- Bedrock API 지연 시간 모니터링

## 📖 참고 자료

- [GitHub 저장소](https://github.com/Twodragon0/amazon-bedrock-knowledgebase-slackbot) - 소스 코드
- [블로그 포스트](https://twodragon.tistory.com/673) - 상세 구현 가이드
- [AWS 블로그](https://aws.amazon.com/blogs/machine-learning/create-a-generative-ai-assistant-with-slack-and-amazon-bedrock/) - 원본 AWS 블로그
- [Amazon Bedrock 문서](https://docs.aws.amazon.com/bedrock/)
- [Slack Bolt for Python](https://slack.dev/bolt-python/)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)

## 🤝 기여

기여를 환영합니다! 자세한 내용은 [CONTRIBUTING.md](./CONTRIBUTING.md)를 참조하세요.

## 📄 라이선스

이 프로젝트는 MIT-0 라이선스 하에 제공됩니다. 자세한 내용은 [LICENSE](./LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- AWS Bedrock 팀 - RAG 기능 제공
- Slack Bolt 팀 - Python 프레임워크
- 원작자: Barry Conway, Dean Colcott

---

**작성자**: [Twodragon](https://twodragon.tistory.com)  
**강의 블로그**: [클라우드 시큐리티 강의](https://twodragon.tistory.com/category/*%20Twodragon/보안%20강의%20%28Course%29)  
**구현 가이드**: [Amazon Bedrock Knowledge Base Slack Bot](https://twodragon.tistory.com/673)  
**GitHub 저장소**: [amazon-bedrock-knowledgebase-slackbot](https://github.com/Twodragon0/amazon-bedrock-knowledgebase-slackbot)  
**마지막 업데이트**: 2025-01-27

---

## 📊 DevSecOps/FinOps/DevOps 체크리스트

### DevSecOps 보안 체크리스트

- [x] KMS 암호화 활성화 (S3, DynamoDB, Lambda 환경 변수)
- [x] Secrets Manager를 통한 시크릿 관리
- [x] IAM 최소 권한 원칙 적용
- [x] CloudTrail 로깅 활성화
- [x] Bedrock Guardrails 설정
- [x] 입력 검증 및 위험 패턴 감지
- [x] SSL/TLS 강제
- [x] S3 버킷 공개 접근 차단

### FinOps 비용 최적화 체크리스트

- [x] 리소스 태깅 (비용 추적)
- [x] Lambda 메모리 및 타임아웃 최적화
- [x] S3 Lifecycle 정책 설정
- [x] CloudWatch 비용 알람 설정
- [x] Budget 설정 (선택적)
- [x] 로깅 레벨 최적화 (비용 절감)
- [x] 모델 사용량 모니터링

### DevOps 운영 체크리스트

- [x] CloudWatch 대시보드 생성
- [x] 알람 설정 (에러, 지속 시간, 쓰로틀)
- [x] 커스텀 메트릭 발행
- [x] 로그 수집 및 보관 정책
- [x] 중복 이벤트 방지
- [x] 에러 핸들링 및 복원력
- [x] CDK를 통한 Infrastructure as Code

---

## 🔧 추가 최적화 옵션

### 향후 개선 사항

1. **VPC 엔드포인트**: 프라이빗 연결을 통한 데이터 전송 (비용 및 보안 향상)
2. **WAF**: API Gateway에 WAF 규칙 추가
3. **프로비저닝된 동시성**: Lambda 프로비저닝된 동시성 설정
4. **캐싱**: API Gateway 응답 캐싱
5. **비용 이상 탐지**: Cost Anomaly Detection 활성화
6. **자동 스케일링**: 필요시 Auto Scaling 설정
