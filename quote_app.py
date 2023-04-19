import config
import requests
from gtts import gTTS
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = config.LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET = config.LINE_CHANNEL_SECRET

DEEPL_API_LEY = config.DEEPL_API_KEY
DEEPL_URL = "https://api-free.deepl.com/v2/translate"

QUOTE_API_KEY = config.QUOTE_API_KEY
QUOTE_URL = "https://api.api-ninjas.com/v1/quotes?category="

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # LINEパラメータの取得
    line_user_id = event.source.user_id
    line_message = event.message.text

    print(line_message)
    reply_message = line_message

    # 英語で書かれた名言を取得する
    if "名言" in line_message:
        response = requests.get(QUOTE_URL, headers={'X-Api-Key': QUOTE_API_KEY})
        if response.status_code == requests.codes.ok:
            quote = response.json()[0]["quote"]
            author = response.json()[0]["author"]
            english_text = "{}\n〜 {}".format(quote, author)
        else:
            print("quote api error:", response.status_code, response.text)
            return

        # 名言を日本語に翻訳する
        params = {
            "auth_key" : DEEPL_API_LEY,
            "text" : english_text,
            "source_lang" : "EN",
            "target_lang" : "JA"
        }

        response = requests.post(DEEPL_URL, params)
        translate_text = response.json()["translations"][0]["text"]
        reply_message = "【English】\n{}\n\n【日本語】\n{}〜".format(english_text, translate_text)
    else:
        reply_message = line_message

    # メッセージを送信する
    line_bot_api.push_message(line_user_id, TextSendMessage(reply_message))

    # 音声変換した英語テキストを送信する
    audio_text = gTTS(english_text, lang='en') 
    #audio_text.save('audio_english_text.mp3')

if __name__ == "__main__":
    app.run(host="localhost", port=8000)
