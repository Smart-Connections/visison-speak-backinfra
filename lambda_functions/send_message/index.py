import boto3
import json
import os
import uuid
import datetime
import openai
from boto3.dynamodb.conditions import Key

openai.api_key = os.environ["OPENAI_API_KEY"]

dynamodbClient = boto3.client("dynamodb")
dynamodb = boto3.resource("dynamodb")
chat_threads_table_name = os.environ["CHAT_THREADS_TABLE_NAME"]
chat_messages_table_name = os.environ["CHAT_MESSAGES_TABLE_NAME"]


def lambda_handler(event, context):
    # DynamoDBオブジェクトを取得
    chat_threads_table = dynamodb.Table(chat_threads_table_name)
    chat_messages_table = dynamodb.Table(chat_messages_table_name)
    # requestContext 内の authorizer オブジェクトからクレームを取得
    claims = event["requestContext"]["authorizer"]["claims"]
    # Cognito の UserID (sub claim) を取得
    cognito_user_id = claims["sub"]
    # API Gatewayからのイベントデータの解析
    body = json.loads(event["body"])
    message = body.get("message", '')
    chat_thread_id = body["chat_thread_id"]

    response = chat_threads_table.get_item(
        Key={
            "chat_thread_id": chat_thread_id,
        }
    )

    if not response["Item"]:
        return {"statusCode": 403, "body": json.dumps({"message": "Not authorized."})}

    chat_thread = response["Item"]

    if not chat_thread["cognito_user_id"] == cognito_user_id:
        return {"statusCode": 403, "body": json.dumps({"message": "Not authorized."})}

    if chat_thread["topic"] == "":
        return {
            "statusCode": 404,
            "body": json.dumps({"message": "This thread's topic is null"}),
        }

    # スレッド一覧取得で最新のものが一番上にくるように
    # updated_timestamp更新
    chat_threads_table.update_item(
        Key={"chat_thread_id": chat_thread["chat_thread_id"]},
        UpdateExpression="SET updated_timestamp = :value",
        ExpressionAttributeValues={":value": int(
            datetime.datetime.now().timestamp())},
        ReturnValues="UPDATED_NEW",
    )

    user_sended_chat_message = {
        "chat_message_id": str(uuid.uuid4()),
        "chat_thread_id": chat_thread["chat_thread_id"],
        "cognito_user_id": chat_thread["cognito_user_id"],
        "sender_type": "USER",
        "english_message": message,
        "japanese_message": "",
        "created_timestamp": int(datetime.datetime.now().timestamp()),
    }

    # テーブルに保存
    chat_messages_table.put_item(Item=user_sended_chat_message)

    res = dynamodbClient.query(
        TableName='chat_messages-prod',
        IndexName='chat_thread_id',
        KeyConditionExpression="chat_thread_id = :chat_thread_id",
        ExpressionAttributeValues={
            ":chat_thread_id": {"S": chat_thread["chat_thread_id"]}
        },
        ScanIndexForward=True
    )
    print("res", res)
    print(res["Items"])
    chat_gpt_result = call_chat_gpt(res["Items"], chat_thread["topic"])
    arguments_str = chat_gpt_result["choices"][0]["message"]["function_call"]["arguments"]
    arguments_dict = json.loads(arguments_str)
    english_message = arguments_dict["english_message"]
    japanese_translated_message = arguments_dict["japanese_translated_message"]

    ai_sended_chat_message = {
        "chat_message_id": str(uuid.uuid4()),
        "chat_thread_id": chat_thread["chat_thread_id"],
        "cognito_user_id": chat_thread["cognito_user_id"],
        "sender_type": "AI",
        "english_message": english_message,
        "japanese_message": japanese_translated_message,
        "created_timestamp": int(datetime.datetime.now().timestamp()),
    }
    # テーブルに保存
    chat_messages_table.put_item(Item=ai_sended_chat_message)

    return {
        "statusCode": 201,
        "body": json.dumps(
            {
                "english_message": ai_sended_chat_message["english_message"],
                "japanese_message": ai_sended_chat_message["japanese_message"],
            }
        ),
    }


def call_chat_gpt(messages, topic):

    functions = [
        {
            "name": "create_response_messages",
            "description": "ユーザーへのメッセージを英語と日本語で生成する。",
            "parameters": {
                "type": "object",
                "properties": {
                    "english_message": {
                        "type": "string",
                        "description": "英語のメッセージ",
                    },
                    "japanese_translated_message": {
                        "type": "string",
                        "description": "日本語訳されたメッセージ",
                    },
                },
                "required": [
                    "english_message",
                    "japanese_translated_message",
                ],
            },
        }
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=format_data(messages, topic),
        functions=functions,
        function_call={"name": "create_response_messages"},
    )

    return completion


def format_data(original_data, topic):
    formatted_data = [
        {
            "role": "system",
            "content": f"あなたはAIチャットボットです。ユーザーから画像が送られました。ユーザーから送られた画像には「{topic}」が映っています。「{topic}」について、英語でユーザーと会話してください。日本語訳した文章も追加で生成する必要があります。リアクション良く会話をしてください。1メッセージは60単語以内で簡潔にしてください",
        }
    ]
    for item in original_data:
        sender_type = item.get('sender_type', {}).get('S', "")
        if sender_type.lower() == 'user':
            role = 'user'
        elif sender_type.lower() == 'ai':
            role = 'assistant'
        else:
            role = sender_type
        formatted_item = {
            "role": role,
            "content": item.get('english_message', {}).get('S', "")
        }
        formatted_data.append(formatted_item)
    print("formatted_data", formatted_data)
    return formatted_data
