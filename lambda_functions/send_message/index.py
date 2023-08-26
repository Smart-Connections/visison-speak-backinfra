import boto3
import json
import os
import uuid
import datetime
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource(
    "dynamodb",
)
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
    message = body["message"]
    # TODO 音声ファイルのbase64エンコード文字列が来た場合の変数
    # message_voice = body["message_voice"]
    chat_thread_id = body["chat_thread_id"]

    response = chat_threads_table.query(
        KeyConditionExpression=Key("chat_thread_id").eq(chat_thread_id),
    )

    if not response["Items"]:
        return {"statusCode": 403, "body": json.dumps({"message": "Not authorized."})}

    chat_thread = response["Items"][0]

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
    ########################################################
    # TODO 音声ファイルが来た場合の処理を追加すること
    ########################################################

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

    ########################################################
    # TODO ChatGPTのAPIを叩く処理を実装すること
    ########################################################

    ai_sended_chat_message = {
        "chat_message_id": str(uuid.uuid4()),
        "chat_thread_id": chat_thread["chat_thread_id"],
        "cognito_user_id": chat_thread["cognito_user_id"],
        "sender_type": "AI",
        "english_message": "Hello, World!",  # とりあえずハードコード
        "japanese_message": "ハロー、ワールド！",  # とりあえずハードコード
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
