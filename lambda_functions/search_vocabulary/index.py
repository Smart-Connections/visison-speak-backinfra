import json
import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

def lambda_handler(event, context):
    # API Gatewayからのイベントデータの解析
    body = json.loads(event["body"])
    keyword = body["keyword"]
    situation = body["situation"]
    style = body["style"]
    difficulty = body["difficulty"]
    type = body["type"]

    chat_gpt_result = call_chat_gpt(keyword, situation, style, difficulty, type)
    arguments_str = chat_gpt_result["choices"][0]["message"]["function_call"]["arguments"]
    arguments_dict = json.loads(arguments_str)
    print(arguments_str, arguments_dict)
    english_vocabulary_list = [
        arguments_dict["1"],
        arguments_dict["2"],
        arguments_dict["3"],
        arguments_dict["4"],
        arguments_dict["5"],
    ]

    return {
        "statusCode": 201,
        "body": json.dumps({"english_vocabulary_list": english_vocabulary_list}),
    }

def call_chat_gpt(keyword, situation, style, difficulty, type):

    functions = [
        {
            "name": "search_english_vocabulary",
            "description": f"ユーザーから送られたキーワードと条件に合致する{type}を5つ返す",
            "parameters": {
                "type": "object",
                "properties": {
                    "1": {
                        "type": "string",
                        "description": f"{type}1",
                    },
                    "2": {
                        "type": "string",
                        "description": f"{type}2",
                    },
                    "3": {
                        "type": "string",
                        "description": f"{type}3",
                    },
                    "4": {
                        "type": "string",
                        "description": f"{type}4",
                    },
                    "5": {
                        "type": "string",
                        "description": f"{type}5",
                    },
                },
                "required": [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                ],
            },
        }
    ]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[
            {
                "role": "system",
                "content": f""""
                あなたは英語学習アプリのアシスタントです。英語学習者に言われた条件の英語{type}を5つ返却してください。条件は以下です。
                キーワード：{keyword}
                シチュエーション：{situation}
                スタイル：{style}
                難易度：{difficulty}
                """,
            }
        ],
        functions=functions,
        function_call={"name": "search_english_vocabulary"},
    )

    return completion