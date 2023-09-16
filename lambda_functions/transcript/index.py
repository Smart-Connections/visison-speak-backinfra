import json
import os
import openai
import base64

openai.api_key = os.environ["OPENAI_API_KEY"]

def lambda_handler(event, context):
    # API Gatewayからのイベントデータの解析
    body = json.loads(event["body"])
    # base64でエンコードされた音声データ
    message_voice = body["message_voice"]
    
    # whisper apiを呼び出してメッセージを取得
    whisper_api_result = call_whisper_api(message_voice)
    print("whisper_api_result: ", whisper_api_result)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "text": whisper_api_result,
            }
        ),
    }

def call_whisper_api(base64_audio_string):
    file_path = '/tmp/audio.mp3'
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(base64_audio_string))

    with open(file_path, 'rb') as f:
        return openai.Audio.transcribe(
            file = f,
            model = "whisper-1",
            response_format="text",
            language="en"
        )
