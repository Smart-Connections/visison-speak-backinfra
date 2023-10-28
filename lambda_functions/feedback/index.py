import json
import os
import openai

from enum import Enum

openai.api_key = os.environ["OPENAI_API_KEY"]


def lambda_handler(event, context):
    # API Gatewayからのイベントデータの解析
    body = json.loads(event["body"])
    message = body.get("message", '')
    words = body.get("words", '')

    result = call_chat_gpt(message, words)
    arguments_str = result["choices"][0]["message"]["function_call"]["arguments"]
    arguments_dict = json.loads(arguments_str)
    print(arguments_str, arguments_dict)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "evaluation": arguments_dict["evaluation"],
                "feedback": arguments_dict["feedback"],
                "feedback_for_target_word": arguments_dict["feedback_for_target_word"],
            }
        ),
    }


def call_chat_gpt(message, words):

    functions = [
        {
            "name": "create_response_messages",
            "description": "ユーザーの英語を評価し、改善点を挙げる",
            "parameters": {
                "type": "object",
                "properties": {
                    "evaluation": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "description": "ユーザーの英語の評価, 1 は GOOD, 2 は IMPLEMENTABLE, そして 3 は BAD."
                    },
                    "feedback": {
                        "type": "string",
                        "description": "ユーザーの英語へのフィードバック",
                    },
                    "feedback_for_target_word": {
                        "type": "string",
                        "description": "ユーザーが目標にしている英単語へのフィードバック",
                    },
                },
                "required": [
                    "evaluation",
                    "feedback",
                    "feedback_for_target_word",
                ],
            },
        }
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=format_data(message, words),
        functions=functions,
        function_call={"name": "create_response_messages"},
    )

    return completion


def format_data(message, words):
    formatted_data = [
        {
            "role": "system",
            "content": f"あなたはAIチャットボットです。ユーザーと英会話をしました。会話内容について、ユーザーがより自然な英語が話せるようにフィードバックをしてください。また、ユーザーが会話の中で使うことを目標にしていた英単語は{words}です。メッセージにこれらが含まれていたら、使い方に対してもフィードバックをしてください。1メッセージは60単語以内で簡潔にしてください",
        }
    ]
    formatted_data.append({
        "role": "user",
        "content": message,
    })
    print("formatted_data", formatted_data)
    return formatted_data


class Evaluation(Enum):
    GOOD = 1
    IMPLEMENTABLE = 2
    BAD = 3
