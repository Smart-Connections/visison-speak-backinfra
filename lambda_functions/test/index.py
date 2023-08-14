import datetime
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    response = {
        "message": "hello world",
        "now": datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
        "TEST_VALUE_1": os.environ["TEST_VALUE_1"],
        "TEST_VALUE_2": os.environ["TEST_VALUE_2"],
        "TEST_VALUE_3": os.environ["TEST_VALUE_3"],
    }
    logger.info({"event": event, "context": context, "response": response})
    return {
        "statusCode": 200,
        "body": json.dumps(response),
    }
