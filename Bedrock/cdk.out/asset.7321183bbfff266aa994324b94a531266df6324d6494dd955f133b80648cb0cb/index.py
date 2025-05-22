import os
import json
import logging
import sys
import time
from pip._internal import main

main(['install', '-I', '-q','boto3','requests','opensearch-py==2.4.2', 'urllib3','--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0,'/tmp/')

import boto3
import requests
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
from botocore.exceptions import NoCredentialsError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_opensearch_client(endpoint):
    service = "aoss" if "aoss" in endpoint else "es"
    logger.debug(f"Connecting to OpenSearch service: {service} at {endpoint}")
    return OpenSearch(
        hosts=[
            {
                "host": endpoint,
                "port": 443,
            }
        ],
        http_auth=AWSV4SignerAuth(
            boto3.Session().get_credentials(), os.getenv("AWS_REGION"), service
        ),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        pool_maxsize=10,
    )

def create_index(client, index_name, body=None):
    """인덱스 생성 함수"""
    try:
        # 기본 인덱스 설정이 제공되지 않은 경우
        if body is None:
            body = {
                'settings': {
                    'index': {
                        'knn': True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                'mappings': {
                    "properties": {
                        "bedrock-knowledge-base-default-vector": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                                "name": "hnsw",
                                "engine": "faiss",
                                "parameters": {},
                                "space_type": "l2"
                            }
                        },
                        "AMAZON_BEDROCK_METADATA": {
                            "type": "text",
                            "index": "false"
                        },
                        "AMAZON_BEDROCK_TEXT_CHUNK": {
                            "type": "text",
                            "index": "true"
                        }
                    }
                }
            }
        
        # 인덱스가 이미 존재하는지 확인
        if client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return True
            
        # 인덱스 생성
        response = client.indices.create(index=index_name, body=body)
        logger.info(f"Index created successfully: {response}")
        
        # 인덱스 생성 확인
        for i in range(5):  # 최대 5번 시도
            if client.indices.exists(index=index_name):
                logger.info(f"Index {index_name} exists after creation")
                return True
            logger.info(f"Waiting for index {index_name} to be available... (attempt {i+1})")
            time.sleep(5)  # 5초 대기
            
        return False
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        return False

def handler(event, context):
    logger.info('Received event: %s', json.dumps(event, indent=2))
    print(event)
    # Parse the JSON string in the Payload field
    #payload_str = event['ResourceProperties']['Create']['parameters']['Payload']
    #payload = json.loads(payload_str) 
    opensearch_endpoint = event['Endpoint']
    index_name = event['IndexName']
    print(opensearch_endpoint)
    opensearch_client = get_opensearch_client(opensearch_endpoint)

    try:
        # 인덱스 존재 확인 요청 처리
        if event['RequestType'] == 'Check':
            try:
                # 인덱스가 존재하는지 확인
                exists = opensearch_client.indices.exists(index=index_name)
                if exists:
                    logger.info(f"Index {index_name} exists and is ready")
                    return {"statusCode": 200, "body": "Index exists"}
                else:
                    # 인덱스가 없으면 생성
                    logger.info(f"Index {index_name} does not exist, creating it now")
                    create_index(opensearch_client, index_name)
                    return {"statusCode": 200, "body": "Index created"}
            except Exception as e:
                logger.error(f"Error checking index: {str(e)}")
                # 오류 발생 시 인덱스 생성 시도
                create_index(opensearch_client, index_name)
                return {"statusCode": 200, "body": f"Error checking index, attempted creation: {str(e)}"}
                
        elif event['RequestType'] == 'Create' :

            params = {
                'index': index_name,
                'body': {
                    'settings': {
                        'index': {
                            'knn': True,
                            "knn.algo_param.ef_search": 512
                        }
                    },
                    'mappings': {
                        "properties":
                      {
                          "bedrock-knowledge-base-default-vector":
                          {
                              "type": "knn_vector",
                              "dimension": 1024,
                              "method":
                              {
                                  "name": "hnsw",
                                  "engine": "faiss",
                                  "parameters":
                                  {},
                                  "space_type": "l2"
                              }
                          },
                          "AMAZON_BEDROCK_METADATA":
                          {
                              "type": "text",
                              "index": "false"
                          },
                          "AMAZON_BEDROCK_TEXT_CHUNK":
                          {
                              "type": "text",
                              "index": "true"
                          }
                      }
                    }
                }
            }

            create_index(opensearch_client, index_name, params['body'])

        elif event['RequestType'] == 'Delete':
            try:
                opensearch_client.indices.delete(index=index_name)
            except Exception as e:
                logger.error(e)

    except NoCredentialsError:
        logger.error('Credentials not available.')