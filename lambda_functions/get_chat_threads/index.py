import boto3
import json
import os
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource(
    "dynamodb",
)
s3_client = boto3.client("s3")
chat_threads_table_name = os.environ["CHAT_THREADS_TABLE_NAME"]
chat_messages_table_name = os.environ["CHAT_MESSAGES_TABLE_NAME"]
bucket_name = os.environ["BUCKET_NAME"]


def generate_presigned_url(object_key, expiration=300):
    try:
        # 署名付きURLの生成
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
            HttpMethod="GET",
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None


def lambda_handler(event, context):
    # DynamoDBオブジェクトを取得
    chat_threads_table = dynamodb.Table("chat_threads")
    chat_messages_table = dynamodb.Table("chat_messages")
    # requestContext 内の authorizer オブジェクトからクレームを取得
    claims = event["requestContext"]["authorizer"]["claims"]
    # Cognito の UserID (sub claim) を取得
    cognito_user_id = claims["sub"]

    # chat_threadsテーブルからcognito_user_idに一致するアイテムを取得
    response = chat_threads_table.query(
        KeyConditionExpression=Key("cognito_user_id").eq(cognito_user_id)
    )

    # chat_threadsのアイテムをupdated_timestampでソート
    chat_threads_items = response["Items"]
    sorted_chat_threads = sorted(
        chat_threads_items, key=lambda x: x["updated_timestamp"], reverse=True
    )

    # レスポンスのフォーマットを作成
    formatted_response = {"chat_threads": []}
    for thread in sorted_chat_threads:
        # chat_messagesテーブルから最新のメッセージを取得
        response = chat_messages_table.query(
            KeyConditionExpression=Key("chat_thread_id").eq(thread["chat_thread_id"]),
            Limit=1,
            ScanIndexForward=False,
        )

        latest_message = response["Items"][0] if response["Items"] else None

        formatted_response["chat_threads"].append(
            {
                "chat_thread_id": thread["chat_thread_id"],
                "image_url": generate_presigned_url(thread["image_path"]),
                "topic": thread["topic"],
                "updated_timestamp": thread["updated_timestamp"],
                "latest_message": {
                    "english_message": latest_message["english_message"],
                    "read": latest_message["read"],
                }
                if latest_message
                else None,
            }
        )

    return {"statusCode": 200, "body": json.dumps(formatted_response)}
