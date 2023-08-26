import boto3
import json
import os
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

    chat_thread_id = event["queryStringParameters"]["chat_thread_id"]
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

    # chat_threadsテーブルからcognito_user_idに一致するアイテムを取得
    response = chat_messages_table.query(
        IndexName="chat_thread_id",
        KeyConditionExpression=Key("chat_thread_id").eq(chat_thread["chat_thread_id"]),
        ScanIndexForward=True,
    )

    chat_messages = response["Items"]

    # レスポンスを作成
    formatted_response = {"chat_messages": []}
    for chat_message in chat_messages:
        formatted_response["chat_messages"].append(
            {
                "sender_type": chat_message["sender_type"],
                "english_message": chat_message["english_message"],
                "japanese_message": chat_message["japanese_message"],
                "created_timestamp": int(chat_message["created_timestamp"]),
            }
        )

    return {"statusCode": 200, "body": json.dumps(formatted_response)}
