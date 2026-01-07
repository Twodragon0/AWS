// # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// # SPDX-License-Identifier: MIT-0.

// '''
// AWS Lambda hosted Slack ChatBot integration to Amazon Bedrock Knowledge Base.
// Supporting Bedrock Knowledge Base with Opensearch as the Vector DB
// Expects Slack Bot Slash Command given by the SLACK_SLASH_COMMAND param and presents 

// The user query is used in a Bedrock KB ReteriveandGenerate API call and the KB 
// response is presented to the user in Slack.

// Slack integration based on SlackBolt library and examples given at:
// https://github.com/slackapi/bolt-python/blob/main/examples/aws_lambda/lazy_aws_lambda.py
 
// __version__ = "0.0.1"
// __status__ = "Development"
// __copyright__ = "Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved."
// __author__ = "Barry Conway <https://www.linkedin.com/in/baconway/>"
// __author__ = "Dean Colcott <https://www.linkedin.com/in/deancolcott/>"

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { execSync } from 'child_process';

// Import L2 constructs
import * as iam from 'aws-cdk-lib/aws-iam';
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as bedrock from 'aws-cdk-lib/aws-bedrock';
import * as ops from 'aws-cdk-lib/aws-opensearchserverless';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cr from 'aws-cdk-lib/custom-resources';
import * as logs from 'aws-cdk-lib/aws-logs';
import { NagSuppressions } from 'cdk-nag';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatch_actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as cloudtrail from 'aws-cdk-lib/aws-cloudtrail';

// RAG Query MODEL_ID (Update dependent on model access and AWS Regional Support):
// Amazon Titan Models: "amazon.titan-text-premier-v1:0"
// Anthropic Claude2  Models:  "anthropic.claude-instant-v1" || "anthropic.claude-v2:1"
// Anthropic Claude3  Models:  "anthropic.claude-3-haiku-20240307-v1:0" || "anthropic.claude-3-sonnet-20240229-v1:0" || "anthropic.claude-3-5-sonnet-20240620-v1:0" 
const RAG_MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0";

// RAG Embeddings Model ID (Update dependent on model access and AWS Regional Support):
// Amazon Titan Embedding: "amazon.titan-embed-text-v1" || "amazon.titan-embed-text-v2:0"
// Cohere Embedding: "cohere.embed-english-v3" // Note: Needs dimension value updated to 1024 in Vector DB.
const EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0";

// Update only to suit custom Slack apps - no change needed for demo.
const SLACK_SLASH_COMMAND = "/ask-aws";
const COLLECTION_NAME = 'slack-bedrock-vector-db';
const VECTOR_INDEX_NAME = 'slack-bedrock-os-index';
const BEDROCK_KB_NAME = 'slack-bedrock-kb';
const BEDROCK_KB_DATA_SOURCE = 'slack-bedrock-kb-ds';
const LAMBDA_MEMORY_SIZE = 265;

// AWS Account params. 
const AWS_ACCOUNT = process.env.CDK_DEFAULT_ACCOUNT;

export class AmazonBedrockKnowledgebaseSlackbotStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DevSecOps: 리소스 태깅 추가 (FinOps 비용 추적)
    const commonTags = {
      Project: 'Bedrock-SlackBot',
      Environment: 'Production',
      ManagedBy: 'CDK',
      CostCenter: 'DevSecOps',
      Owner: 'DevSecOps-Team',
      Purpose: 'AIOps-Chatbot'
    };

    // DevSecOps: KMS 키 생성 (암호화 강화) - 먼저 생성하여 다른 리소스에서 사용
    const encryptionKey = new kms.Key(this, 'EncryptionKey', {
      enableKeyRotation: true,
      description: 'KMS key for Slack bot data encryption',
      removalPolicy: cdk.RemovalPolicy.RETAIN, // 보안: 키는 유지
      alias: 'bedrock-slackbot-encryption-key'
    });
    
    // KMS 키 태깅
    cdk.Tags.of(encryptionKey).add('Name', 'bedrock-slackbot-kms-key');
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(encryptionKey).add(key, value);
    });

    // Get secrets from context or use default values for development
    const slackBotToken = this.node.tryGetContext('slackBotToken') || 'dummy-token-for-development';
    const slackSigningSecret = this.node.tryGetContext('slackSigningSecret') || 'dummy-secret-for-development';
    
    // Log warning if using default values
    if (slackBotToken === 'dummy-token-for-development' || slackSigningSecret === 'dummy-secret-for-development') {
      console.warn('WARNING: Using dummy values for Slack tokens. For production use, provide real tokens with --context slackBotToken=xxx --context slackSigningSecret=yyy');
    }

    // Create secrets in Secrets Manager
    const slackBotTokenSecret = new secretsmanager.Secret(this, 'SlackBotTokenSecret', {
      secretName: '/slack/bot-token',
      description: 'Slack Bot User OAuth Token',
      secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({
        token: slackBotToken
      }))
    });

    const slackBotSigningSecret = new secretsmanager.Secret(this, 'SlackBotSigningSecret', {
      secretName: '/slack/signing-secret',
      description: 'Slack Signing Secret',
      secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({
        secret: slackSigningSecret
      }))
    });

    // Create SSM parameters that reference the secrets
    const botTokenParameter = new ssm.StringParameter(this, 'SlackBotTokenParameter', {
      parameterName: '/slack/bot-token/parameter',
      stringValue: `{{resolve:secretsmanager:${slackBotTokenSecret.secretName}}}`,
      description: 'Reference to Slack Bot Token in Secrets Manager',
      tier: ssm.ParameterTier.STANDARD
    });

    const signingSecretParameter = new ssm.StringParameter(this, 'SlackSigningSecretParameter', {
      parameterName: '/slack/signing-secret/parameter',
      stringValue: `{{resolve:secretsmanager:${slackBotSigningSecret.secretName}}}`,
      description: 'Reference to Slack Signing Secret in Secrets Manager',
      tier: ssm.ParameterTier.STANDARD
    });

    // define an s3 bucket with FinOps optimization
    const s3Bucket = new s3.Bucket(this, 'kb-bucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL, 
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: encryptionKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true, 
      enforceSSL: true,
      versioned: true,
      // FinOps: Lifecycle 정책으로 비용 최적화
      lifecycleRules: [
        {
          id: 'transition-to-ia',
          enabled: true,
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30)
            }
          ]
        },
        {
          id: 'transition-to-glacier',
          enabled: true,
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(90)
            }
          ]
        },
        {
          id: 'delete-old-versions',
          enabled: true,
          noncurrentVersionExpiration: cdk.Duration.days(365)
        }
      ]
    });
    
    // 태깅 적용
    cdk.Tags.of(s3Bucket).add('Name', 'bedrock-kb-bucket');
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(s3Bucket).add(key, value);
    });
    NagSuppressions.addResourceSuppressions(s3Bucket, [
      { id: 'AwsSolutions-S1', reason: 'S3 access logging not required for sample code' }
    ]);

    // Create an IAM policy for S3 access
    const s3AccessListPolicy = new PolicyStatement({
      actions: ['s3:ListBucket'],
      resources: [s3Bucket.bucketArn],
    });
    s3AccessListPolicy.addCondition("StringEquals", {"aws:ResourceAccount": AWS_ACCOUNT});

    // Create an IAM policy for S3 access
    const s3AccessGetPolicy = new iam.PolicyStatement({
      actions: ['s3:GetObject','s3:Delete*'],
      resources: [`${s3Bucket.bucketArn}/*`],
    });
    s3AccessGetPolicy.addCondition("StringEquals", {"aws:ResourceAccount": AWS_ACCOUNT});

    // Create an IAM policy to invoke Bedrock models and access titan v1 embedding model
    const bedrockExecutionRolePolicy = new PolicyStatement();
    bedrockExecutionRolePolicy.addActions("bedrock:InvokeModel");
    bedrockExecutionRolePolicy.addResources(`arn:aws:bedrock:${cdk.Stack.of(this).region}::foundation-model/${EMBEDDING_MODEL}`);

    // Create an IAM policy to delete Bedrock knowledgebase
    const bedrockKBDeleteRolePolicy = new PolicyStatement();
    bedrockKBDeleteRolePolicy.addActions("bedrock:Delete*");
    bedrockKBDeleteRolePolicy.addResources(`arn:aws:bedrock:${this.region}:${this.account}:knowledge-base/*`);

    // Create IAM policy to call OpensearchServerless
    const BedrockOSSPolicyForKnowledgeBase = new PolicyStatement();
    BedrockOSSPolicyForKnowledgeBase.addActions("aoss:APIAccessAll");
    BedrockOSSPolicyForKnowledgeBase.addActions("aoss:DeleteAccessPolicy","aoss:DeleteCollection","aoss:DeleteLifecyclePolicy","aoss:DeleteSecurityConfig","aoss:DeleteSecurityPolicy");
    BedrockOSSPolicyForKnowledgeBase.addResources(`arn:aws:aoss:${this.region}:${this.account}:collection/*`);

    // Define IAM Role and add Iam policies for bedrock execution role
    const bedrockExecutionRole = new iam.Role(this, 'BedrockExecutionRole', {
      assumedBy: new iam.ServicePrincipal('bedrock.amazonaws.com'),
    });
    bedrockExecutionRole.addToPolicy(bedrockExecutionRolePolicy);
    bedrockExecutionRole.addToPolicy(BedrockOSSPolicyForKnowledgeBase);
    bedrockExecutionRole.addToPolicy(s3AccessListPolicy);
    bedrockExecutionRole.addToPolicy(s3AccessGetPolicy);
    bedrockExecutionRole.addToPolicy(bedrockKBDeleteRolePolicy);

    // Create bedrock Guardrails for the slack bot
    const Guardrail = new bedrock.CfnGuardrail(this, 'MyGuardrail', {
      blockedInputMessaging: 'Sorry, the Ask AWS Well Architected slack bot cannot provide a response for this question',
      blockedOutputsMessaging: 'Sorry, the Ask AWS Well Architected slack bot cannot provide a response for this question',
      name: 'slack-bedrock-guardrail',
      description: 'Bedrock Guardrails for Slack bedrock bot',
    
      contentPolicyConfig: {
        filtersConfig: [
          {
              'type': 'SEXUAL',
              'inputStrength': 'HIGH',
              'outputStrength': 'HIGH'
          },
          {
              'type': 'VIOLENCE',
              'inputStrength': 'HIGH',
              'outputStrength': 'HIGH'
          },
          {
              'type': 'HATE',
              'inputStrength': 'HIGH',
              'outputStrength': 'HIGH'
          },
          {
              'type': 'INSULTS',
              'inputStrength': 'HIGH',
              'outputStrength': 'HIGH'
          },
          {
              'type': 'MISCONDUCT',
              'inputStrength': 'HIGH',
              'outputStrength': 'HIGH'
          },
          {
              'type': 'PROMPT_ATTACK',
              'inputStrength': 'HIGH',
              'outputStrength': 'NONE'
          }
        ],
      },
      sensitiveInformationPolicyConfig: {
        piiEntitiesConfig: [{
          'type': 'EMAIL',
          'action': 'ANONYMIZE'
        },
        {
          'type': 'PHONE',
          'action': 'ANONYMIZE'
        },
        {
          'type': 'NAME',
          'action': 'ANONYMIZE'
        },
        {
          'type': 'CREDIT_DEBIT_CARD_NUMBER',
          'action': 'BLOCK'
        }],
      },
      wordPolicyConfig: {
        managedWordListsConfig: [{
          type: 'PROFANITY',
        }],
      },
    });

    const GuardrailVersion = new bedrock.CfnGuardrailVersion(this, 'MyGuardrailVersion', {
      guardrailIdentifier: Guardrail.attrGuardrailId, //guardrailIdentifier
      description: 'v1.0',
    });

    //Define vars for Guardrail ID and version for the Retrieve&Generate API call
    const GUARD_RAIL_ID = Guardrail.attrGuardrailId
    const GUARD_RAIL_VERSION = GuardrailVersion.attrVersion
    
    // Define OpenSearchServerless Collection & depends on policies
    const osCollection = new ops.CfnCollection(this, 'osCollection', {
      name: COLLECTION_NAME,
      description: 'Slack bedrock vector db',
      type: 'VECTORSEARCH'
    });

    // Define AOSS vector DB encryption policy with AWSOwned key true
    const aossEncryptionPolicy = new ops.CfnSecurityPolicy(this, 'aossEncryptionPolicy', {
      name: "bedrock-kb-encryption-policy",
      type: "encryption",
      policy: JSON.stringify({
        Rules: [
          {
            ResourceType: 'collection',
            Resource: [`collection/${COLLECTION_NAME}`]
          }
        ],
        AWSOwnedKey: true
      }),
    });
    osCollection.addDependency(aossEncryptionPolicy);

    // Define Vector DB network policy with AllowFromPublic true. include collection & dashboard
    const aossNetworkPolicy = new ops.CfnSecurityPolicy(this, 'aossNetworkPolicy', {
      name: 'bedrock-kb-network-policy',
      type: 'network',
      policy: JSON.stringify([
        {
          Rules: [
            {
              ResourceType: 'collection',
              Resource: [`collection/${COLLECTION_NAME}`],
            },
            {
              ResourceType: 'dashboard',
              Resource: [`collection/${COLLECTION_NAME}`],
            },
          ],
          AllowFromPublic: true,
        },
      ]),
    });
    osCollection.addDependency(aossNetworkPolicy);

    // Define createIndexFunction execution role and policy
    const createIndexFunctionRole = new iam.Role(this, 'CreateIndexFunctionRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    createIndexFunctionRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'));
    createIndexFunctionRole.addToPolicy(new PolicyStatement({
      actions: [
        'aoss:APIAccessAll',
        'aoss:DescribeIndex',
        'aoss:ReadDocument',
        'aoss:CreateIndex',
        'aoss:DeleteIndex',
        'aoss:UpdateIndex',
        'aoss:WriteDocument',
        'aoss:CreateCollectionItems',
        'aoss:DeleteCollectionItems',
        'aoss:UpdateCollectionItems',
        'aoss:DescribeCollectionItems'
      ],
      resources: [
        `arn:aws:aoss:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:collection/*`,
        `arn:aws:aoss:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:index/*`
      ],
      effect: iam.Effect.ALLOW,
    }));

    // Define a lambda function to create an opensearch serverless index
    const createIndexFunction = new lambda.Function(this, 'CreateIndexFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset('lambda/CreateIndexFunction'),
      environment: {
        "INDEX_NAME": osCollection.attrId,
      },
      handler: 'index.handler',
      timeout: cdk.Duration.minutes(1),
      role: createIndexFunctionRole
    });

    // Define OpenSearchServerless access policy
    const aossAccessPolicy = new ops.CfnAccessPolicy(this, 'aossAccessPolicy', {
      name: 'bedrock-kb-access-policy',
      type: 'data',
      policy: JSON.stringify([
        {
        Rules: [
          {
            ResourceType: "collection",
            Resource: [`collection/*`],
            Permission: ["aoss:*"],
          },
          {
            ResourceType: 'index',
            Resource: [`index/*/*`],
            Permission: ['aoss:*'],
          },
        ],
        Principal: [
          bedrockExecutionRole.roleArn,
          createIndexFunction.role?.roleArn,
          `arn:aws:iam::${this.account}:root`
        ],
      }
    ]),
    });
    osCollection.addDependency(aossAccessPolicy);
    
    const Endpoint = `${osCollection.attrId}.${cdk.Stack.of(this).region}.aoss.amazonaws.com`;

    const vectorIndex = new cr.AwsCustomResource(this, 'vectorIndex', {
      installLatestAwsSdk: true,
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: createIndexFunction.functionName,
          InvocationType: 'RequestResponse',
          Payload: JSON.stringify({
            RequestType: 'Create',
            CollectionName: osCollection.name,
            IndexName: VECTOR_INDEX_NAME,
            Endpoint: Endpoint,
          }),
        },
        physicalResourceId: cr.PhysicalResourceId.of(Date.now().toString()),
      },
      onDelete: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: createIndexFunction.functionName,
          InvocationType: 'RequestResponse',
          Payload: JSON.stringify({
            RequestType: 'Delete',
            CollectionName: osCollection.name,
            IndexName: VECTOR_INDEX_NAME,
            Endpoint: Endpoint,
          }),
        },
      },
      policy: cr.AwsCustomResourcePolicy.fromStatements([
        new iam.PolicyStatement({
          actions: ['lambda:InvokeFunction'],
          resources: [createIndexFunction.functionArn],
        }),
      ]),
      timeout: cdk.Duration.seconds(60),
    });

    // Ensure vectorIndex depends on collection and access policy
    vectorIndex.node.addDependency(osCollection);
    vectorIndex.node.addDependency(aossAccessPolicy);
    vectorIndex.node.addDependency(createIndexFunction);

    // 벡터 인덱스 생성 확인을 위한 대기 시간 추가
    const waitForIndexCreation = new cr.AwsCustomResource(this, 'waitForIndexCreation', {
      installLatestAwsSdk: true,
      onCreate: {
        service: 'Lambda',
        action: 'invoke',
        parameters: {
          FunctionName: createIndexFunction.functionName,
          InvocationType: 'RequestResponse',
          Payload: JSON.stringify({
            RequestType: 'Check',
            IndexName: VECTOR_INDEX_NAME,
            Endpoint: Endpoint,
          }),
        },
        physicalResourceId: cr.PhysicalResourceId.of('waitForIndexCreation-' + Date.now().toString()),
      },
      policy: cr.AwsCustomResourcePolicy.fromStatements([
        new iam.PolicyStatement({
          actions: ['lambda:InvokeFunction'],
          resources: [createIndexFunction.functionArn],
        }),
      ]),
      timeout: cdk.Duration.seconds(120),
    });
    
    // 인덱스 생성 확인 리소스가 벡터 인덱스에 의존하도록 설정
    waitForIndexCreation.node.addDependency(vectorIndex);

    // Define a Bedrock knowledge base with type opensearch serverless and titan for embedding model
    const bedrockkb = new bedrock.CfnKnowledgeBase(this, 'bedrockkb', {
      name: BEDROCK_KB_NAME,
      description: 'bedrock knowledge base for aws',
      roleArn: bedrockExecutionRole.roleArn,
      knowledgeBaseConfiguration: {
        type: 'VECTOR',
        vectorKnowledgeBaseConfiguration: {
          embeddingModelArn: `arn:aws:bedrock:${cdk.Stack.of(this).region}::foundation-model/${EMBEDDING_MODEL}`
        },
      },
      storageConfiguration: {
        type: 'OPENSEARCH_SERVERLESS',
        opensearchServerlessConfiguration: {
          collectionArn: osCollection.attrArn, 
          fieldMapping: {
            vectorField: 'bedrock-knowledge-base-default-vector',
            textField: 'AMAZON_BEDROCK_TEXT_CHUNK',
            metadataField: 'AMAZON_BEDROCK_METADATA'
          },
          vectorIndexName: VECTOR_INDEX_NAME
        },
      },
    });

    // Add explicit dependencies for bedrock kb
    bedrockkb.node.addDependency(waitForIndexCreation); // 인덱스 생성 확인 리소스에 의존
    bedrockkb.node.addDependency(vectorIndex);
    bedrockkb.node.addDependency(osCollection);
    bedrockkb.node.addDependency(aossAccessPolicy);
    bedrockkb.node.addDependency(bedrockExecutionRole);
    bedrockkb.node.addDependency(createIndexFunction);

    // Define a bedrock knowledge base data source with S3 bucket
    const bedrockKbDataSource = new bedrock.CfnDataSource(this, 'bedrockKbDataSource', {
      name: BEDROCK_KB_DATA_SOURCE,
      knowledgeBaseId: bedrockkb.attrKnowledgeBaseId,
      dataSourceConfiguration: {
        type: 'S3',
        s3Configuration: {
          bucketArn: s3Bucket.bucketArn
        }
      }
    });
    
    // Add dependency to ensure data source is created after knowledge base
    bedrockKbDataSource.node.addDependency(bedrockkb);

    // Create an IAM policy to allow the lambda to invoke models in Amazon Bedrock
    const lambdaBedrockModelPolicy = new PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["bedrock:InvokeModel"],
      resources: [`arn:aws:bedrock:${cdk.Stack.of(this).region}::foundation-model/${RAG_MODEL_ID}`],
      conditions: {
          "StringEquals": {"aws:ResourceAccount": this.account}
      }
  });

    // Add explicit permissions for RetrieveAndGenerate operation
    const lambdaBedrockOperationsPolicy = new PolicyStatement()
    lambdaBedrockOperationsPolicy.addActions(
      "bedrock:InvokeModel",
      "bedrock:Retrieve",
      "bedrock:RetrieveAndGenerate",
      "bedrock:GetFoundationModel",
      "bedrock:ListFoundationModels",
      "bedrock:GetInferenceProfile"
    )
    lambdaBedrockOperationsPolicy.addResources("*")
    lambdaBedrockOperationsPolicy.addCondition("StringEquals", {"aws:ResourceAccount": this.account})

    // Create an IAM policy to allow the lambda to call Retrieve and Retrieve and Generate on a Bedrock Knowledge Base 
    const lambdaBedrockKbPolicy = new PolicyStatement();
    lambdaBedrockKbPolicy.addActions("bedrock:Retrieve");
    lambdaBedrockKbPolicy.addActions("bedrock:RetrieveAndGenerate");
    lambdaBedrockKbPolicy.addResources(`arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:knowledge-base/${bedrockkb.attrKnowledgeBaseId}`);

    // Additional permissions for models like Claude 3.5 Sonnet
    const lambdaBedrockAdditionalModelPolicy = new PolicyStatement()
    lambdaBedrockAdditionalModelPolicy.addActions(
      "bedrock:GetInferenceProfile",
      "bedrock:ListInferenceProfiles",
      "bedrock:InvokeModel",
      "bedrock:GetModelInvocationLoggingConfiguration"
    )
    lambdaBedrockAdditionalModelPolicy.addResources("*")
    lambdaBedrockAdditionalModelPolicy.addCondition("StringEquals", {"aws:ResourceAccount": this.account})

    // Create an IAM policy to allow the lambda to call SSM
    const lambdaSSMPolicy = new PolicyStatement();
    lambdaSSMPolicy.addActions("ssm:GetParameter");
    lambdaSSMPolicy.addResources(`arn:aws:ssm:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:parameter${botTokenParameter.parameterName}`);
    lambdaSSMPolicy.addResources(`arn:aws:ssm:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:parameter${signingSecretParameter.parameterName}`);
    
    const lambdaReinvokePolicy = new PolicyStatement();
    lambdaReinvokePolicy.addActions("lambda:InvokeFunction");
    lambdaReinvokePolicy.addResources(`arn:aws:lambda:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:function:AmazonBedrock*`);

    const lambdaGRinvokePolicy = new PolicyStatement();
    lambdaGRinvokePolicy.addActions("bedrock:ApplyGuardrail");
    lambdaGRinvokePolicy.addResources(`arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:guardrail/*`);


    // DynamoDB 테이블 먼저 생성
    const eventTrackingTable = new dynamodb.Table(this, 'SlackEventTrackingTable', {
      tableName: 'SlackEventTracking',
      partitionKey: { name: 'event_id', type: dynamodb.AttributeType.STRING },
      timeToLiveAttribute: 'expiry_time',
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: encryptionKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      pointInTimeRecovery: false
    });

    // DevSecOps: CloudTrail 로깅 설정
    const trail = new cloudtrail.Trail(this, 'BedrockSlackbotTrail', {
      trailName: 'bedrock-slackbot-cloudtrail',
      enableFileValidation: true,
      includeGlobalServiceEvents: true,
      isMultiRegionTrail: false,
      sendToCloudWatchLogs: true,
      cloudWatchLogsRetention: logs.RetentionDays.ONE_MONTH
    });
    
    // CloudTrail 태깅
    cdk.Tags.of(trail).add('Name', 'bedrock-slackbot-trail');
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(trail).add(key, value);
    });

    // FinOps: Lambda 메모리 최적화 (512MB -> 256MB로 조정, 필요시 조정)
    // DevOps: 타임아웃 최적화 (10분 -> 5분)
    const bedrockKbSlackbotFunction = new lambda.Function(this, 'BedrockKbSlackbotFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      memorySize: 256, // FinOps: 비용 최적화를 위해 메모리 감소
      environment: {
        "RAG_MODEL_ID": RAG_MODEL_ID,
        "SLACK_SLASH_COMMAND": SLACK_SLASH_COMMAND,
        "KNOWLEDGEBASE_ID": bedrockkb.attrKnowledgeBaseId,
        "SLACK_BOT_TOKEN_PARAMETER": botTokenParameter.parameterName,
        "SLACK_SIGNING_SECRET_PARAMETER": signingSecretParameter.parameterName,
        "GUARD_RAIL_ID": GUARD_RAIL_ID,
        "GUARD_RAIL_VERSION": GUARD_RAIL_VERSION,
        "EVENT_TRACKING_TABLE": eventTrackingTable.tableName,
        "PREVENT_DUPLICATES": "true",
        "EVENT_ID_SALT": cdk.Names.uniqueId(this),
        "EVENT_TTL_SECONDS": "900"
      },
      handler: 'index.handler',
      code: lambda.Code.fromAsset('lambda/BedrockKbSlackbotFunction', {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [],
          local: {
            tryBundle(outputDir: string) {
              try {
                execSync('pip3 --version');
              } catch {
                return false;
              }

              const commands = [
                `cd lambda/BedrockKbSlackbotFunction`,
                `pip3 install -r requirements.txt -t ${outputDir}`,
                `cp -a . ${outputDir}`
              ];

              execSync(commands.join(' && '));
              return true;
            }
          }
        }
      }),
      timeout: cdk.Duration.minutes(5), // DevOps: 타임아웃 최적화
      // DevSecOps: 환경 변수 암호화
      environmentEncryption: encryptionKey
    });
    
    // Lambda 함수 태깅
    cdk.Tags.of(bedrockKbSlackbotFunction).add('Name', 'bedrock-kb-slackbot-function');
    Object.entries(commonTags).forEach(([key, value]) => {
      cdk.Tags.of(bedrockKbSlackbotFunction).add(key, value);
    });

    // Lambda 삭제 정책 설정
    const cfnFunction = bedrockKbSlackbotFunction.node.defaultChild as lambda.CfnFunction;
    cfnFunction.cfnOptions.deletionPolicy = cdk.CfnDeletionPolicy.DELETE;
    cfnFunction.cfnOptions.updateReplacePolicy = cdk.CfnDeletionPolicy.DELETE;

     // Grant the Lambda function permission to read the secrets
     slackBotTokenSecret.grantRead(bedrockKbSlackbotFunction);
     slackBotSigningSecret.grantRead(bedrockKbSlackbotFunction);

    // Attach listed IAM policies to the Lambda functions Execution role
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaBedrockModelPolicy)
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaBedrockOperationsPolicy)
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaBedrockKbPolicy)
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaBedrockAdditionalModelPolicy)  // Add additional permissions only
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaReinvokePolicy)
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaGRinvokePolicy)
    bedrockKbSlackbotFunction.addToRolePolicy(lambdaSSMPolicy)

    // Create an IAM role for API Gateway CloudWatch Logs
    const apiGatewayLogsRole = new iam.Role(this, 'ApiGatewayLogsRole', {
      assumedBy: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonAPIGatewayPushToCloudWatchLogs')
      ]
    });

    // Configure account-level API Gateway logging setting
    const apiGatewayAccountConfig = new apigateway.CfnAccount(this, 'ApiGatewayAccount', {
      cloudWatchRoleArn: apiGatewayLogsRole.roleArn
    });

    // Create a single log group instance
    const apiGatewayLogGroup = new logs.LogGroup(this, 'ApiGatewayAccessLogs', {
      retention: logs.RetentionDays.ONE_WEEK, // Add log retention policy
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    // Create API Gateway with CloudWatch logging enabled
    const api = new apigateway.RestApi(this, 'BedrockKbSlackbotApi', {
      deployOptions: {
        stageName: 'prod',
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
        tracingEnabled: true,
        accessLogDestination: new apigateway.LogGroupLogDestination(apiGatewayLogGroup),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields()
      }
    });
    
    // Ensure that API Gateway depends on the account configuration
    api.node.addDependency(apiGatewayAccountConfig);

    // Add access log settings to the API Gateway stage, but without CloudWatchRoleArn
    const stage = api.deploymentStage.node.defaultChild as apigateway.CfnStage;
    stage.addPropertyOverride('AccessLogSetting', {
      DestinationArn: apiGatewayLogGroup.logGroupArn,
      Format: JSON.stringify({
        requestId: '$context.requestId',
        ip: '$context.identity.sourceIp',
        caller: '$context.identity.caller',
        user: '$context.identity.user',
        requestTime: '$context.requestTime',
        httpMethod: '$context.httpMethod',
        resourcePath: '$context.resourcePath',
        status: '$context.status',
        protocol: '$context.protocol',
        responseLength: '$context.responseLength'
      })
    });
    stage.addPropertyOverride('TracingEnabled', true);

    // Define the '/slack/ask-aws' API resource with a POST method
    const bedrockKbSlackbotResource = api.root.addResource('slack').addResource('ask-aws');
    bedrockKbSlackbotResource.addMethod('POST', new apigateway.LambdaIntegration(bedrockKbSlackbotFunction));

    // CDK NAG Suppression Rules - IAM
    //============================================
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockExecutionRole/DefaultPolicy/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/CreateIndexFunctionRole/DefaultPolicy/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotFunction/ServiceRole/DefaultPolicy/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/CreateIndexFunctionRole/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/AWS679f53fac002430cb0da5b7982bd2287/ServiceRole/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotFunction/ServiceRole/Resource'
      ],
      [
        { id: 'AwsSolutions-IAM5', reason: 'IAM policy ARN limits actions to the AWS Account and AWS Service with conditions' },
        { id: 'AwsSolutions-IAM4', reason: 'IAM managed policies used for sample/demo code' }
      ]
    );

    // CDK NAG Suppression Rules - Secrets Manager
    //============================================
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/AmazonBedrockKnowledgebaseSlackbotStack/SlackBotTokenSecret/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/SlackBotSigningSecret/Resource',
      ],
      [
        { id: 'AwsSolutions-SMG4', reason: 'Secret rotation is not possible in this case' },
      ]
    );

    // CDK NAG Suppression Rules - API GW
    //============================================
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotApi/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotApi/DeploymentStage.prod/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotApi/DeploymentStage.prod/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotApi/Default/slack/ask-aws/POST/Resource',
        '/AmazonBedrockKnowledgebaseSlackbotStack/BedrockKbSlackbotApi/Default/slack/ask-aws/POST/Resource',
      ],
      [
        { id: 'AwsSolutions-APIG2', reason: 'API validation is not required for demo/sample code' },
        { id: 'AwsSolutions-APIG3', reason: 'AWS WAF is not required for sample/demo code' },
        { id: 'AwsSolutions-APIG6', reason: 'Logging is enabled for the API' },
        { id: 'AwsSolutions-APIG4', reason: 'API Auth is not provided in demo/sample code' },
        { id: 'AwsSolutions-COG4', reason: 'Cognito is not being used in the sample code' }
      ]
    );

    // Additional CDK NAG Suppression Rules
    //============================================
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/AmazonBedrockKnowledgebaseSlackbotStack/ApiGatewayLogsRole/Resource',
      ],
      [
        { id: 'AwsSolutions-IAM4', reason: 'AWS managed policy is required for API Gateway CloudWatch logs' },
      ]
    );

    // Suppress CdkNagValidationFailure for Custom Resource
    NagSuppressions.addResourceSuppressionsByPath(
      this,
      [
        '/AmazonBedrockKnowledgebaseSlackbotStack/AWS679f53fac002430cb0da5b7982bd2287/Resource',
      ],
      [
        { id: 'AwsSolutions-L1', reason: 'Custom resource is required for vector index creation' },
        { id: 'CdkNagValidationFailure', reason: 'Suppressing validation error for intrinsic functions' },
      ]
    );

    // DynamoDB 테이블 접근 권한 추가
    eventTrackingTable.grantReadWriteData(bedrockKbSlackbotFunction);
    
    // DynamoDB ListTables 권한 추가
    const dynamoDbListTablesPolicy = new PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:ListTables',
        'dynamodb:DescribeTable',
        'dynamodb:CreateTable'
      ],
      resources: [`arn:aws:dynamodb:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:table/*`]
    });
    
    bedrockKbSlackbotFunction.addToRolePolicy(dynamoDbListTablesPolicy);
    
    // DevOps: CloudWatch 대시보드 생성
    const dashboard = new cloudwatch.Dashboard(this, 'BedrockSlackbotDashboard', {
      dashboardName: 'Bedrock-Slackbot-Monitoring'
    });
    
    // Lambda 메트릭 위젯
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda Invocations',
        left: [bedrockKbSlackbotFunction.metricInvocations()],
        width: 12
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Errors',
        left: [bedrockKbSlackbotFunction.metricErrors()],
        width: 12
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration',
        left: [bedrockKbSlackbotFunction.metricDuration()],
        width: 12
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Throttles',
        left: [bedrockKbSlackbotFunction.metricThrottles()],
        width: 12
      })
    );
    
    // DevOps: SNS 토픽 생성 (알람용)
    const alarmTopic = new sns.Topic(this, 'BedrockSlackbotAlarmTopic', {
      topicName: 'bedrock-slackbot-alarms',
      displayName: 'Bedrock Slackbot Alarms'
    });
    
    // DevOps: Lambda 에러 알람
    const lambdaErrorAlarm = new cloudwatch.Alarm(this, 'LambdaErrorAlarm', {
      metric: bedrockKbSlackbotFunction.metricErrors({
        statistic: 'Sum',
        period: cdk.Duration.minutes(1)
      }),
      threshold: 5,
      alarmName: 'bedrock-slackbot-lambda-errors',
      alarmDescription: 'Alert when Lambda function errors exceed threshold',
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      datapointsToAlarm: 2,
      evaluationPeriods: 2
    });
    lambdaErrorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));
    
    // DevOps: Lambda 지속 시간 알람 (FinOps: 비용 최적화)
    const lambdaDurationAlarm = new cloudwatch.Alarm(this, 'LambdaDurationAlarm', {
      metric: bedrockKbSlackbotFunction.metricDuration({
        statistic: 'Average',
        period: cdk.Duration.minutes(1)
      }),
      threshold: 300000, // 5분 (밀리초)
      alarmName: 'bedrock-slackbot-lambda-duration',
      alarmDescription: 'Alert when Lambda function duration exceeds 5 minutes (cost optimization)',
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      datapointsToAlarm: 2,
      evaluationPeriods: 2
    });
    lambdaDurationAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));
    
    // DevOps: Lambda 쓰로틀 알람
    const lambdaThrottleAlarm = new cloudwatch.Alarm(this, 'LambdaThrottleAlarm', {
      metric: bedrockKbSlackbotFunction.metricThrottles({
        statistic: 'Sum',
        period: cdk.Duration.minutes(1)
      }),
      threshold: 1,
      alarmName: 'bedrock-slackbot-lambda-throttles',
      alarmDescription: 'Alert when Lambda function is throttled',
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      datapointsToAlarm: 1,
      evaluationPeriods: 1
    });
    lambdaThrottleAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));
    
    // FinOps: API Gateway 비용 알람 (요청 수 기반)
    const apiGatewayRequests = api.metricCount({
      statistic: 'Sum',
      period: cdk.Duration.hours(1)
    });
    
    const apiGatewayCostAlarm = new cloudwatch.Alarm(this, 'ApiGatewayCostAlarm', {
      metric: apiGatewayRequests,
      threshold: 10000, // 시간당 10,000 요청
      alarmName: 'bedrock-slackbot-api-cost',
      alarmDescription: 'Alert when API Gateway requests exceed cost threshold',
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      datapointsToAlarm: 1,
      evaluationPeriods: 1
    });
    apiGatewayCostAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(alarmTopic));
    
    // FinOps: Budget 설정 (월 예산 알람)
    // 주의: Budget은 AWS 계정 레벨 리소스이므로 CDK로 관리하기보다는 
    // AWS 콘솔이나 AWS CLI를 사용하여 설정하는 것을 권장합니다.
    // 
    // Budget 설정 방법:
    // 1. AWS 콘솔: Billing > Budgets > Create budget
    // 2. AWS CLI: 
    //    aws budgets create-budget --account-id <account-id> --budget file://budget.json
    // 
    // budget.json 예시:
    // {
    //   "BudgetName": "bedrock-slackbot-monthly-budget",
    //   "BudgetLimit": {
    //     "Amount": "100",
    //     "Unit": "USD"
    //   },
    //   "TimeUnit": "MONTHLY",
    //   "BudgetType": "COST",
    //   "CostFilters": {
    //     "TagKeyValue": ["user:Project$Bedrock-SlackBot"]
    //   }
    // }
    
    // 모든 리소스에 태깅 적용
    cdk.Tags.of(this).add('Project', 'Bedrock-SlackBot');
    cdk.Tags.of(this).add('Environment', 'Production');
    cdk.Tags.of(this).add('ManagedBy', 'CDK');
    cdk.Tags.of(this).add('CostCenter', 'DevSecOps');
}
}
