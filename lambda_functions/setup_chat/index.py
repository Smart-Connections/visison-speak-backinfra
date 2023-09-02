import datetime
import time
import json
import base64
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging
import os
import uuid
import mimetypes

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

logger = logging.getLogger()
logger.setLevel(logging.INFO)
env = os.environ.get("ENV")
dynamodb = boto3.resource(
    "dynamodb",
)
s3_client = boto3.client("s3")
azure_account_region = os.environ["AZURE_ACCOUNT_REGION"]
azure_account_key = os.environ["AZURE_ACCOUNT_KEY"]
bucket_name = os.environ["BUCKET_NAME"]

credentials = CognitiveServicesCredentials(azure_account_key)
client = ComputerVisionClient(
    endpoint="https://" + azure_account_region + ".api.cognitive.microsoft.com/",
    credentials=credentials,
)


def get_file_extension(original_filename):
    # ファイルの拡張子を取得
    _, file_extension = os.path.splitext(original_filename)
    return file_extension


def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


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
    chat_threads_table = dynamodb.Table(os.environ["CHAT_THREADS_TABLE_NAME"])

    # requestContext 内の authorizer オブジェクトからクレームを取得
    claims = event["requestContext"]["authorizer"]["claims"]
    # Cognito の UserID (sub claim) を取得
    user_id = claims["sub"]

    # デバッグ用に出力しておくが、不要になったら消すこと
    print(event)

    # API Gatewayからのイベントデータの解析
    body = json.loads(event["body"])
    image_data = body["image"]
    filename = body["filename"]
    # Base64デコード
    decoded_image = base64.b64decode(image_data)

    extension = get_file_extension(filename)
    content_type = get_content_type(filename)
    chat_thread_id = str(uuid.uuid4())
    filename = f"{str(uuid.uuid4())}{extension}"
    s3_object_key = f"users/{user_id}/chat_threads/{chat_thread_id}/{filename}"

    s3_client.put_object(
        Bucket=bucket_name,
        Key=s3_object_key,
        Body=decoded_image,
        ContentType=content_type,
    )

    created_timestamp = int(datetime.datetime.now().timestamp())
    chat_thread = {
        "chat_thread_id": chat_thread_id,
        "cognito_user_id": user_id,
        "image_path": s3_object_key,
        "topic": "",
        "created_timestamp": created_timestamp,
        "updated_timestamp": created_timestamp,
    }

    # テーブルに保存
    chat_threads_table.put_item(Item=chat_thread)

    presigned_url = generate_presigned_url(object_key=s3_object_key)

    image_analysis_description = client.analyze_image(
        presigned_url, visual_features=[VisualFeatureTypes.description])
    image_analysis_tags = client.analyze_image(
        presigned_url, visual_features=[VisualFeatureTypes.tags])

    description = image_analysis_description.description.captions[0].text
    tags = [{"tag": tag.name, "confidence": tag.confidence} for tag in image_analysis_tags.tags]

    return {
        "statusCode": 201,
        "body": json.dumps(
            {
                "chat_thread_id": chat_thread_id,
                "presigned_url": presigned_url,
                "description": description,
                "tags": tags,   
            }
        ),
    }
