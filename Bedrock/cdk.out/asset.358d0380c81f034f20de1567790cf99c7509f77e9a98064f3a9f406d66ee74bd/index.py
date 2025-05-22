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
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

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
  logging.info(f"Bedrock Knowledge Base Response: {response}")
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
        logger.info(f"Shortcut triggered – message: {message_text}")

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
            logger.error(f"Bedrock 호출 오류: {e}")
            answer = f"Bedrock 모델 호출 중 오류가 발생했습니다: {str(e)}"

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
            logger.error(f"Slack 메시지 전송 오류: {e}")
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
        # 멘션된 메시지 텍스트 추출
        message_text = event.get("text", "")
        # 봇 ID 추출 및 멘션 부분 제거
        user_id = event.get("user")
        bot_id_pattern = r'<@[A-Z0-9]+>'
        import re
        message_text = re.sub(bot_id_pattern, '', message_text).strip()
        
        # 스레드 정보 확인
        thread_ts = event.get("thread_ts", event.get("ts"))
        channel_id = event.get("channel")
        
        logger.info(f"멘션 이벤트 감지: {message_text}, 채널: {channel_id}, 스레드: {thread_ts}")
        
        # 보안 관련 키워드 확인
        security_keywords = ["취약점", "보안", "CVE", "패치", "업데이트"]
        
        # Bedrock 모델 호출
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": f"""다음 보안 이슈를 DevSecOps 관점에서 분석하고 한국어로 평가해주세요.
이모티콘, 코드 블록, 목록을 적절히 활용하여 시각적으로 구조화된 응답을 제공해주세요.

{message_text}

다음 항목들을 포함하여 분석해주세요:

1. :warning: 취약점 분석:
   - 취약점 유형 및 심각도
   - 영향받는 시스템 및 서비스
   - 잠재적 위험 및 영향도
   - CVE 정보 분석

2. :gear: 대응 방안:
   - 패치 적용 우선순위
   - 임시 조치 방안
   - 업데이트 절차
   - 롤백 계획

3. :chart_with_upwards_trend: 모니터링 및 자동화:
   - 취약점 스캔 자동화
   - 패치 적용 모니터링
   - 영향도 분석 자동화
   - 알림 설정

4. :shield: AWS 보안 최적화:
   - AWS Security Hub 연계 방안
   - GuardDuty 활용 방안
   - AWS Config 규칙 설정
   - CloudWatch 알림 구성

5. :link: 참고 자료:
   - 관련 보안 권고문 링크
   - AWS 보안 관련 문서
   - 모범 사례 문서"""
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
        
        # 응답 전송 - client.chat_postMessage 사용하여 명시적으로 스레드에 답변
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,  # 명시적으로 원본 메시지의 스레드에 응답
            text=(
                f":shield: *보안 취약점 분석 결과* :shield:\n\n"
                f":page_facing_up: *분석 대상*\n```{message_text}```\n\n"
                f"{answer}\n\n"
                f":information_source: *참고*\n"
                f"• 이 분석은 DevSecOps 관점에서 수행되었습니다.\n"
                f"• AWS 보안 서비스를 활용한 대응 방안이 포함되어 있습니다.\n"
                f"• 추가 질문이 있으시면 `@Bedrock-agent`를 멘션해주세요."
            )
        )
        
    except Exception as e:
        logger.error(f"멘션 처리 오류: {str(e)}")
        try:
            # 오류 발생 시에도 스레드에 응답
            thread_ts = event.get("thread_ts", event.get("ts"))
            channel_id = event.get("channel")
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="멘션 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            )
        except Exception as e2:
            logger.error(f"오류 메시지 전송 실패: {str(e2)}")

# ────────────────────────────────────────────────────────────────────────────────

# Init the Slack Bolt logger and log handlers. 
SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)

# Lambda handler method.
def handler(event, context):
    try:
        # Initialize SlackRequestHandler
        slack_handler = SlackRequestHandler(app=app)
        
        # Process the event
        response = slack_handler.handle(event, context)
        
        # 응답이 없는 경우 기본 응답 반환
        if not response:
            return {
                "statusCode": 200,
                "body": ""
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Handler 오류: {str(e)}")
        return {
            "statusCode": 200,  # Slack은 항상 200 응답을 기대함
            "body": ""
        }

