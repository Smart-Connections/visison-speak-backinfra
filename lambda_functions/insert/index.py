import datetime
import time
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
env = os.environ.get("ENV")


def lambda_handler(event, context):
    # requestContext 内の authorizer オブジェクトからクレームを取得
    claims = event["requestContext"]["authorizer"]["claims"]

    # Cognito の UserID (sub claim) を取得
    user_id = claims["sub"]
    params = json.loads(event["body"])
    item = {
        "UserId": user_id,
        "Name": params["name"],
        "Timestamp": int(time.mktime(datetime.datetime.now().timetuple())),
    }
    logger.info(item)

    dynamodb = boto3.resource(
        "dynamodb",
    )
    table = dynamodb.Table(os.environ["TABLE_NAME"])

    try:
        table.put_item(Item=item)
        logger.info("登録に成功しました。")
    except (BotoCoreError, ClientError) as error:
        logger.error("error: {}".format(error))
        return json.dumps({"statusCode": 500})
    return {
        "statusCode": 201,
        "body": json.dumps({"item": item}),
    }
