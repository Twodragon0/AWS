# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0.
#

'''
AWS Lambda hosted Slack ChatBot integration to Amazon Bedrock Knowledge Base. 
Expects Slack Bot Slash Command given by the SLACK_SLASH_COMMAND param and presents 
a user query to the Bedrock Knowledge Base described by the KNOWLEDGEBASE_ID parameter.

The user query is used in a Bedrock KB ReteriveandGenerate API call and the KB 
response is presented to the user in Slack.

Slack integration based on SlackBolt library and examples given at:
https://github.com/slackapi/bolt-python/blob/main/examples/aws_lambda/lazy_aws_lambda.py
 '''
 
__version__ = "0.0.1"
__status__ = "Development"
__copyright__ = "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved."
__author__ = "Dean Colcott <https://www.linkedin.com/in/deancolcott/>"

import os
import json
import boto3
import logging
import time
import html
import urllib.parse
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# DevSecOps: 로깅 설정 최적화 (FinOps: 비용 절감)
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # DEBUG -> INFO로 변경하여 로그 비용 절감

# DevOps: CloudWatch 메트릭 클라이언트
cloudwatch = boto3.client('cloudwatch')

# DevOps: 커스텀 메트릭 발행 함수
def put_metric(metric_name, value, unit='Count'):
    """CloudWatch 커스텀 메트릭 발행"""
    try:
        cloudwatch.put_metric_data(
            Namespace='BedrockSlackbot',
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': time.time()
                }
            ]
        )
    except Exception as e:
        logger.error(f"메트릭 발행 실패: {str(e)}")

# DevSecOps: 입력 검증 함수
def validate_input(text, max_length=1000):
    """사용자 입력 검증"""
    if not text or not isinstance(text, str):
        return False, "입력이 비어있거나 유효하지 않습니다."
    if len(text) > max_length:
        return False, f"입력이 너무 깁니다. 최대 {max_length}자까지 허용됩니다."
    # 위험한 문자 패턴 검사
    dangerous_patterns = ['<script', 'javascript:', 'onerror=']
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False, "잠재적으로 위험한 입력이 감지되었습니다."
    return True, None

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
# 이벤트 추적을 위한 테이블 이름
EVENT_TABLE_NAME = os.environ.get('EVENT_TRACKING_TABLE', 'SlackEventTracking')

# 이벤트 추적 테이블이 존재하는지 확인하고 없으면 생성
def ensure_event_table_exists():
    try:
        # 테이블 존재 여부 확인 - 직접 describe_table 호출 (더 안전한 방식)
        dynamodb_client = boto3.client('dynamodb')
        try:
            dynamodb_client.describe_table(TableName=EVENT_TABLE_NAME)
            logging.info(f"이벤트 추적 테이블 '{EVENT_TABLE_NAME}' 이미 존재함")
            return True
        except dynamodb_client.exceptions.ResourceNotFoundException:
            # 테이블이 없는 경우 생성
            logging.info(f"이벤트 추적 테이블 '{EVENT_TABLE_NAME}' 생성 시작")
            table = dynamodb.create_table(
                TableName=EVENT_TABLE_NAME,
                KeySchema=[
                    {'AttributeName': 'event_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'event_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'expiry_time'
                }
            )
            # 테이블 생성 완료 대기
            table.meta.client.get_waiter('table_exists').wait(TableName=EVENT_TABLE_NAME)
            logging.info(f"이벤트 추적 테이블 '{EVENT_TABLE_NAME}' 생성 완료")
            return True
    except Exception as e:
        logging.error(f"이벤트 추적 테이블 생성 오류: {str(e)}")
        # 테이블 생성 실패해도 계속 진행 (중복 응답은 허용)
        return False

# 이벤트가 이미 처리되었는지 확인
def is_event_processed(event_id):
    if not event_id:
        return False
    
    try:
        table = dynamodb.Table(EVENT_TABLE_NAME)
        response = table.get_item(
            Key={'event_id': event_id}
        )
        # 아이템이 존재하면 이미 처리된 이벤트
        result = 'Item' in response
        if result:
            logging.info(f"이벤트 {event_id}는 이미 처리되었습니다.")
        else:
            logging.info(f"이벤트 {event_id}는 새로운 이벤트입니다.")
        return result
    except Exception as e:
        logging.error(f"이벤트 확인 오류: {str(e)}")
        # 오류 발생 시 처리 안된 것으로 간주 (안전하게 응답)
        return False

# 이벤트를 처리됨으로 표시
def mark_event_as_processed(event_id):
    if not event_id:
        return False
    
    try:
        # 환경 변수에서 TTL 값 가져오기
        ttl_seconds = int(os.environ.get('EVENT_TTL_SECONDS', '3600'))  # TTL 시간을 1시간으로 늘림
        # TTL 시간 계산 (현재시간 + TTL 초)
        current_time = int(time.time())
        expiry_time = current_time + ttl_seconds
        
        table = dynamodb.Table(EVENT_TABLE_NAME)
        
        # 조건부 쓰기 - 이미 존재하지 않는 경우에만 추가
        response = table.put_item(
            Item={
                'event_id': event_id,
                'processed_at': current_time,
                'expiry_time': expiry_time
            },
            ConditionExpression="attribute_not_exists(event_id)"
        )
        logging.info(f"이벤트 {event_id} 처리 상태 기록 완료: TTL={expiry_time}")
        return True
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        # 이미 존재하는 경우 - 중복 이벤트
        logging.info(f"이벤트 {event_id}는 이미 처리 상태로 기록되어 있음")
        return True
    except Exception as e:
        logging.error(f"이벤트 표시 오류: {str(e)}")
        return False

# Get params from SSM
def get_parameter(parameter_name):
    ssm = boto3.client('ssm')
    try:
        response = ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        # Parse the JSON string from the parameter
        parameter_value = response['Parameter']['Value']
        
        #Remove the JSON structure and extract just the value
        try:
            json_value = json.loads(parameter_value)
            # Get the first value from the dictionary
            value = next(iter(json_value.values()))
            return value
        except (json.JSONDecodeError, StopIteration):
            # If parsing fails or dictionary is empty, return the raw value
            return parameter_value
            
    except Exception as e:
        # SECURITY: Do not log parameter names or error details that might contain sensitive information
        # Only log generic error message without exposing parameter names or values
        error_type = type(e).__name__
        logging.error(f"Error retrieving parameter from SSM: {error_type}")
        # Re-raise with sanitized error message
        raise Exception(f"Failed to retrieve parameter from SSM: {error_type}") from e

# Get parameter names from environment variables
bot_token_parameter = os.environ['SLACK_BOT_TOKEN_PARAMETER']
signing_secret_parameter = os.environ['SLACK_SIGNING_SECRET_PARAMETER']

# Retrieve the parameters
bot_token = get_parameter(bot_token_parameter)
signing_secret = get_parameter(signing_secret_parameter)

# Initialize Slack app
app = App(
    process_before_response=True,
    token=bot_token,
    signing_secret=signing_secret
)

# Get the expected slack and AWS account params to local vars. 
SLACK_SLASH_COMMAND = os.environ['SLACK_SLASH_COMMAND']
KNOWLEDGEBASE_ID = os.environ['KNOWLEDGEBASE_ID'] 
RAG_MODEL_ID = os.environ['RAG_MODEL_ID'] 
AWS_REGION = os.environ['AWS_REGION']
GUARD_RAIL_ID = os.environ['GUARD_RAIL_ID']
GUARD_VERSION = os.environ['GUARD_RAIL_VERSION']

print(f'GR_ID,{GUARD_RAIL_ID}')
print(f'GR_V, {GUARD_VERSION}')

# Initialize Bedrock client
bedrock_client = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

@app.middleware
def log_request(logger, body, next):
    '''
    SlackBolt library logging. 
    '''
    logger.debug(body)
    return next()
def respond_to_slack_within_3_seconds(body, ack):
  '''
    Slack Bot Slash Command requires an Ack response within 3 seconds or it 
    messages an operation timeout error to the user in the chat thread. 

    The SlackBolt library provides a Async Ack function then re-invokes this Lambda 
    to LazyLoad the process_command_request command that calls the Bedrock KB ReteriveandGenerate API.

    This function is called initially to acknowledge the Slack Slash command within 3 secs. 
  '''
  try:
    user_query = body["text"]
    logging.info(f"${SLACK_SLASH_COMMAND} - Acknowledging command: {SLACK_SLASH_COMMAND} - User Query: {user_query}\n")
    ack(f"\n${SLACK_SLASH_COMMAND} - Processing Request: {user_query}")

  except Exception as err:
    print(f"${SLACK_SLASH_COMMAND} - Error: {err}")
    respond(f"${SLACK_SLASH_COMMAND} - Sorry an error occurred. Please try again later. Error: {err}")

def process_command_request(respond, body):
  '''
    Receive the Slack Slash Command user query and proxy the query to Bedrock Knowledge base ReteriveandGenerate API 
    and return the response to Slack to be presented in the users chat thread. 
  '''
  start_time = time.time()
  try:
    # Get the user query
    user_query = body.get("text", "").strip()
    
    # DevSecOps: 입력 검증
    is_valid, error_message = validate_input(user_query)
    if not is_valid:
      logger.warning(f"입력 검증 실패: {error_message}")
      put_metric('InvalidInput', 1)
      respond(f"${SLACK_SLASH_COMMAND} - {error_message}")
      return
    
    logger.info(f"${SLACK_SLASH_COMMAND} - Responding to command: {SLACK_SLASH_COMMAND} - User Query: {html.escape(user_query[:100])}")  # FinOps: 로그 길이 제한

    # DevOps: 메트릭 발행 (요청 수)
    put_metric('CommandRequests', 1)
    
    kb_response = get_bedrock_knowledgebase_response(user_query)
    response_text = kb_response["output"]["text"]
    
    # DevOps: 처리 시간 메트릭
    duration = (time.time() - start_time) * 1000  # 밀리초
    put_metric('CommandDuration', duration, 'Milliseconds')
    
    respond(f"\n${SLACK_SLASH_COMMAND} - Response: {response_text}\n")
    put_metric('CommandSuccess', 1)
  
  except Exception as err:
    # DevOps: 에러 메트릭
    put_metric('CommandErrors', 1)
    logger.error(f"${SLACK_SLASH_COMMAND} - Error: {html.escape(str(err))}")  # DevSecOps: 에러 메시지 이스케이프
    respond(f"${SLACK_SLASH_COMMAND} - Sorry an error occurred. Please try again later.")

def get_bedrock_knowledgebase_response(user_query):
  '''
    Get and return the Bedrock Knowledge Base ReteriveAndGenerate response.
    Do all init tasks here instead of globally as initial invocation of this lambda
    provides Slack required ack in 3 sec. It doesn't trigger any bedrock functions and is 
    time sensitive. 
  '''
  bedrock_start_time = time.time()
  
  try:
    # DevSecOps: 입력 재검증
    is_valid, error_message = validate_input(user_query)
    if not is_valid:
      raise ValueError(error_message)

    #Create the RetrieveAndGenerateCommand input with the user query.
    input =  { 
        "text": user_query
      }

    config = {
      "type" : "KNOWLEDGE_BASE",
      "knowledgeBaseConfiguration": {
          "generationConfiguration": {
              "guardrailConfiguration": {
                  "guardrailId": GUARD_RAIL_ID,
                  "guardrailVersion": GUARD_VERSION
              },
          },
          "knowledgeBaseId": KNOWLEDGEBASE_ID,
          "modelArn": RAG_MODEL_ID
     }
    }

    # DevOps: Bedrock 호출 메트릭
    put_metric('BedrockInvocations', 1)
    
    response = bedrock_client.retrieve_and_generate(
      input=input, retrieveAndGenerateConfiguration=config
    )
    
    # DevOps: Bedrock 응답 시간 메트릭
    bedrock_duration = (time.time() - bedrock_start_time) * 1000
    put_metric('BedrockDuration', bedrock_duration, 'Milliseconds')
    
    # FinOps: 로그 최적화 (전체 응답 대신 요약만 로깅)
    response_summary = {
      'status': 'success',
      'has_output': 'output' in response,
      'duration_ms': round(bedrock_duration, 2)
    }
    logger.info(f"Bedrock Knowledge Base Response: {json.dumps(response_summary)}")
    
    return response
  except Exception as e:
    # DevOps: Bedrock 에러 메트릭
    put_metric('BedrockErrors', 1)
    logger.error(f"Bedrock 호출 오류: {html.escape(str(e))}")
    raise

# Init the Slack Slash '/' command handler.
app.command(SLACK_SLASH_COMMAND)(ack=respond_to_slack_within_3_seconds, lazy=[process_command_request])

# ─── Message Shortcut 처리 핸들러 추가 ─────────────────────────────────────────────
@app.shortcut("aws-chatbot")
def handle_message_shortcut(ack, shortcut, client, logger):
    try:
        # 1) Slack에 3초 내 ACK
        ack()

        # 2) 선택된 메시지 텍스트 추출
        message_text = shortcut["message"]["text"]
        # Use html.escape to sanitize user input before logging
        logger.info(f"Shortcut triggered – message: {html.escape(message_text)}")

        # 3) Bedrock 모델 호출
        try:
            # Claude 모델용 요청 형식
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": f"""다음 이벤트를 분석하고 한국어로 요약해주세요. 
                        주요 내용, 보안 관점에서의 시사점, AWS 서비스 활용 방안을 포함해주세요:
                        
                        {message_text}"""
                    }
                ]
            }

            response = bedrock_client.invoke_model(
                modelId=os.environ["RAG_MODEL_ID"],
                body=json.dumps(request_body)
            )
            
            # 응답 파싱
            response_body = json.loads(response.get("body").read())
            answer = response_body.get("content", [{}])[0].get("text", "응답 생성에 실패했습니다.")
            
        except Exception as e:
            logger.error(f"Bedrock 호출 오류: {html.escape(str(e))}") # Sanitize the error message before logging
            answer = f"Bedrock 모델 호출 중 오류가 발생했습니다: {html.escape(str(e))}"

        # 4) Thread 메시지 전송
        try:
            # 먼저 메시지를 전송하고 thread_ts를 얻음
            response = client.chat_postMessage(
                channel=shortcut["channel"]["id"],
                thread_ts=shortcut["message"]["ts"],  # 원본 메시지의 타임스탬프
                text=(
                    f"> *내용:*\n```{message_text}```\n\n"
                    f"*분석 결과:*\n{answer}"
                )
            )
            logger.info(f"Thread 메시지 전송 성공: {response}")
        except SlackApiError as e:
            logger.error(f"Slack 메시지 전송 오류: {html.escape(str(e))}") # Sanitize the error message before logging
            # 오류 발생 시 빈 응답 반환
            return {
                "statusCode": 200,
                "body": ""
            }
        
    except Exception as e:
        logger.error(f"Shortcut 처리 오류: {str(e)}")
        # 오류 발생 시 빈 응답 반환
        return {
            "statusCode": 200,
            "body": ""
        }

# ──── 멘션 이벤트 처리 핸들러 추가 ───────────────────────────────────────────────
@app.event("app_mention")
def handle_mentions(event, say, client, logger):
    try:
        # 이벤트 ID 확인 - 이벤트 ID와 채널 ID를 조합하여 고유한 식별자 생성
        salt = os.environ.get('EVENT_ID_SALT', '')
        channel_id = event.get("channel", "")
        ts = event.get("event_ts", "")
        # 이벤트 ID를 더 고유하게 만들기 위해 채널 ID와 타임스탬프 조합
        event_id = f"{channel_id}:{ts}:{salt}"
        
        # 로깅 강화
        logger.info(f"멘션 이벤트 수신: ID={event_id}, user={html.escape(event.get('user', ''))}")
        
        # 이미 처리된 이벤트인지 확인 (조건을 좀 더 세밀하게 조정)
        if is_event_processed(event_id):
            logger.info(f"이미 처리된 이벤트 (ID: {event_id}) - 중복 응답 방지")
            return
            
        # 중요: 이벤트를 먼저 처리됨으로 표시 (응답 전에 수행)
        mark_event_as_processed(event_id)
        logger.info(f"이벤트 {event_id} 처리 시작 - DB에 기록 완료")
        
        # 멘션된 메시지 텍스트 추출
        message_text = html.escape(event.get("text", ""))
        # 봇 ID 추출 및 멘션 부분 제거
        user_id = html.escape(event.get("user", ""))
        bot_id_pattern = r'<@[A-Z0-9]+>'
        import re
        message_text = re.sub(bot_id_pattern, '', message_text).strip()
        
        # 스레드 정보 확인
        thread_ts = html.escape(event.get("thread_ts", event.get("ts", "")))
        channel_id = html.escape(event.get("channel", ""))
        
        logger.info(f"멘션 이벤트 감지: {message_text}, 채널: {channel_id}, 스레드: {thread_ts}, 이벤트 ID: {event_id}")
        
        # Bedrock 모델 호출
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": f"""다음 보안 이슈를 분석하고 간결하게 요약해주세요:

{message_text}

아래 지침을 따라 응답해주세요:
1. 최대 10줄 이내로 요약
2. Slack 메시지 포맷팅을 활용해서 가독성을 높이되, 과도하게 사용하지 않기
   - 중요 정보는 *굵게*
   - 제목이나 강조할 부분은 _기울임체_
   - 코드나 명령어는 `코드 블록`
   - 적절한 이모티콘 사용 :warning: :white_check_mark: :gear: :shield:
3. 간결하고 명확한 문장 사용
4. 핵심 취약점, 영향, 대응방안만 포함

다음 구조로 작성해주세요:
- :warning: *취약점 개요*: (1-2줄)
- :globe_with_meridians: *영향 범위*: (1-2줄)
- :unlock: *주요 위험*: (1-2줄)
- :white_check_mark: *대응 방안*: (2-3줄)
- :shield: *AWS 보안 서비스*: (1-2줄)"""
                }
            ]
        }

        logger.info("Bedrock 모델 호출 중...")
        response = bedrock_client.invoke_model(
            modelId=os.environ["RAG_MODEL_ID"],
            body=json.dumps(request_body)
        )
        
        # 응답 파싱
        response_body = json.loads(response.get("body").read())
        answer = response_body.get("content", [{}])[0].get("text", "응답 생성에 실패했습니다.")
        
        logger.info(f"응답 생성 완료: {len(answer)} 자")
        
        # Slack 포맷팅을 적용한 응답 전송 - say() 함수 사용
        say_response = say(
            text=answer,
            channel=channel_id,
            thread_ts=thread_ts
        )
        
        logger.info(f"Slack 응답 전송 완료: {say_response}")
        
    except Exception as e:
        logger.error(f"멘션 처리 오류: {str(e)}")
        try:
            thread_ts = html.escape(event.get("thread_ts", event.get("ts", "")))
            channel_id = html.escape(event.get("channel", ""))
            say(
                text="처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                channel=channel_id,
                thread_ts=thread_ts
            )
        except Exception as e2:
            logger.error(f"오류 메시지 전송 실패: {str(e2)}")

# ────────────────────────────────────────────────────────────────────────────────

# Init the Slack Bolt logger and log handlers.
# FinOps: 로그 레벨을 INFO로 설정하여 비용 절감
SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO  # DEBUG -> INFO로 변경
)

# Lambda handler method.

def handler(event, context):
    try:
        # 로깅 강화
        logging.info(f"Lambda 핸들러 호출: event_type={urllib.parse.quote(event.get('type', 'unknown'))}")
        
        # 중복 이벤트 확인 - app_mention 이벤트인 경우
        if event.get('type') == 'event_callback' and event.get('event', {}).get('type') == 'app_mention':
            # 이벤트 ID 생성
            slack_event = event.get('event', {})
            channel_id = slack_event.get("channel", "")
            ts = slack_event.get("event_ts", "")
            salt = os.environ.get('EVENT_ID_SALT', '')
            event_id = f"{channel_id}:{ts}:{salt}"
            
            try:
                # 이벤트 추적 테이블 확인
                ensure_event_table_exists()
                
                # 이미 처리된 이벤트인지 확인
                if is_event_processed(event_id):
                    logging.info(f"핸들러 레벨에서 중복 이벤트 감지 (ID: {event_id}) - 처리 중단")
                    return {
                        "statusCode": 200,
                        "body": "Event already processed"
                    }
                
                # 이벤트를 처리됨으로 표시
                mark_event_as_processed(event_id)
                logging.info(f"핸들러 레벨에서 이벤트 {event_id} 처리 시작 - DB에 기록 완료")
            except Exception as e:
                logging.error(f"이벤트 중복 확인 중 오류: {str(e)}")
                # 오류 발생 시에도 계속 진행
        
        # Initialize SlackRequestHandler
        slack_handler = SlackRequestHandler(app=app)
        
        # Process the event
        response = slack_handler.handle(event, context)
        logging.info(f"Slack 응답 처리 결과: {html.escape(str(response and response.get('statusCode', 'unknown')))}")
        
        # 응답이 없는 경우 기본 응답 반환
        if not response:
            return {
                "statusCode": 200,
                "body": ""
            }
            
        return response
        
    except Exception as e:
        logging.error(f"Handler 오류: {str(e)}")
        return {
            "statusCode": 200,  # Slack은 항상 200 응답을 기대함
            "body": ""
        }

