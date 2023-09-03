import boto3
import json
import os
import uuid
import datetime
import time
import openai
import base64
from boto3.dynamodb.conditions import Key

openai.api_key = os.environ["OPENAI_API_KEY"]

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
    # base64でエンコードされた音声データ
    message_voice = body.get("message_voice", '')
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
        ExpressionAttributeValues={":value": int(datetime.datetime.now().timestamp())},
        ReturnValues="UPDATED_NEW",
    )
    
    # whisper apiを呼び出してメッセージを取得
    if (message_voice != ""):
        whisper_api_result = call_whisper_api(message_voice)
        message = whisper_api_result["text"]

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

    chat_gpt_result = call_chat_gpt()
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

def call_whisper_api(base64_audio_string):
    file_path = '/tmp/audio.mp3'
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(base64_audio_string))

    with open(file_path, 'rb') as f:
        return openai.Audio.transcribe("whisper-1", f)

def call_chat_gpt():

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
                    "message",
                    "japanese_translated_message",
                ],
            },
        }
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[
            {
                "role": "system",
                "content": "あなたはAIチャットボットです。ユーザーから画像が送られました。ユーザーから送られた画像には「a desk with a computer and a chair」が映っています。「a desk with a computer and a chair」について、英語でユーザーと会話してください。日本語訳した文章も追加で生成する必要があります。",
            },
        ],
        functions=functions,
        function_call={"name": "create_response_messages"},
    )

    return completion