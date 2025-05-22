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
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# DynamoDB 클라이언트 초기화
dynamodb = boto3.resource('dynamodb')
# 이벤트 추적을 위한 테이블 이름
EVENT_TABLE_NAME = os.environ.get('EVENT_TRACKING_TABLE', 'SlackEventTracking')

# 이벤트 추적 테이블이 존재하는지 확인하고 없으면 생성
def ensure_event_table_exists():
    try:
        # 테이블 목록 확인
        existing_tables = list(dynamodb.tables.all())
        table_exists = any(table.name == EVENT_TABLE_NAME for table in existing_tables)
        
        if not table_exists:
            # 테이블 생성
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
        raise  # Re-raise the exception to stop execution

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
        return 'Item' in response
    except Exception as e:
        logging.error(f"이벤트 확인 오류: {str(e)}")
        # 오류 발생 시 처리 안된 것으로 간주 (안전하게 응답)
        return False

# 이벤트를 처리됨으로 표시
def mark_event_as_processed(event_id):
from boto3.dynamodb.conditions import Attr  # Used for safe query construction in DynamoDB

def mark_event_as_processed(event_id):
    if not event_id:
        return False
    
    try:
        # 환경 변수에서 TTL 값 가져오기
        ttl_seconds = int(os.environ.get('EVENT_TTL_SECONDS', '900'))
        # TTL 시간 계산 (현재시간 + TTL 초)
        expiry_time = int(time.time()) + ttl_seconds
        
        table = dynamodb.Table(EVENT_TABLE_NAME)
        table.put_item(
            Item={
                'event_id': Attr('event_id').eq(event_id),
                'processed_at': int(time.time()),
                'expiry_time': expiry_time
            }
        )
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
        print(f"Error getting parameter {parameter_name}: {str(e)}")
        raise e

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
# import html
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
  try:
    # Get the user query
    user_query = body["text"]
    logging.info(f"${SLACK_SLASH_COMMAND} - Responding to command: {SLACK_SLASH_COMMAND} - User Query: {user_query}")

    kb_response = get_bedrock_knowledgebase_response(user_query)
    response_text = kb_response["output"]["text"]
    respond(f"\n${SLACK_SLASH_COMMAND} - Response: {response_text}\n")
  
  except Exception as err:
    print(f"${SLACK_SLASH_COMMAND} - Error: {err}")
    respond(f"${SLACK_SLASH_COMMAND} - Sorry an error occurred. Please try again later. Error: {err}")

def get_bedrock_knowledgebase_response(user_query):
  '''
    Get and return the Bedrock Knowledge Base ReteriveAndGenerate response.
    Do all init tasks here instead of globally as initial invocation of this lambda
    provides Slack required ack in 3 sec. It doesn't trigger any bedrock functions and is 
    time sensitive. 
  '''

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

  response = bedrock_client.retrieve_and_generate(
    input=input, retrieveAndGenerateConfiguration=config
  )
  # import html
  logging.info(f"Bedrock Knowledge Base Response: {html.escape(str(response))}") # Sanitize the response before logging
  logging.info(f"Bedrock Knowledge Base Response: {html.escape(str(response))}") # Sanitize the response before logging
  return response

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
        # import html
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
            # import html
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
        # 이벤트 ID 확인 - 필요한 경우 솔트 추가
        salt = os.environ.get('EVENT_ID_SALT', '')
        # import html  # Used for escaping user input to prevent log injection
        event_id = f"{html.escape(event.get('event_ts', ''))}{salt}"
        
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
SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)

# Lambda handler method.
# Import urllib.parse for URL encoding
# This package is used to sanitize input before logging to prevent log injection attacks
import urllib.parse

def handler(event, context):
    try:
        # 로깅 강화
        logging.info(f"Lambda 핸들러 호출: event_type={urllib.parse.quote(event.get('type', 'unknown'))}")
        
        # 이벤트 추적 테이블 확인
        ensure_event_table_exists()
        
        # Initialize SlackRequestHandler
        slack_handler = SlackRequestHandler(app=app)
        
        # Process the event
        response = slack_handler.handle(event, context)
        # import html
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

