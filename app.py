import os
import pysrt
import deepl
import requests
import base64
from flask import Flask, render_template, request, Response
from dotenv import load_dotenv

app = Flask(__name__)

# 환경 변수 로드
load_dotenv()
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

# 결제 성공 시 승인 요청 처리
@app.route("/success")
def success():
    payment_key = request.args.get("paymentKey")
    order_id = request.args.get("orderId")
    amount = request.args.get("amount")

    # 토스 시크릿 키 (테스트용)
    secret_key = "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"
    encoded_key = base64.b64encode((secret_key + ":").encode()).decode()

    res = requests.post(
        "https://api.tosspayments.com/v1/payments/confirm",
        json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
        headers={"Authorization": f"Basic {encoded_key}", "Content-Type": "application/json"}
    )

    if res.status_code == 200:
        return render_template("index.html", payment_status="success")
    return "Payment failed", 400

@app.route("/translate", methods=["POST"])
def translate_srt():
    file = request.files.get("file")
    src_lang = request.form.get("src_lang", "auto")
    dest_lang = request.form.get("dest_lang", "ko")
    newline_type = request.form.get("newline_type", "crlf")

    if not file or not DEEPL_AUTH_KEY:
        return "Missing file or API Key", 400

    temp_path = "temp.srt"
    file.save(temp_path)

    try:
        translator = deepl.Translator(DEEPL_AUTH_KEY)
        subs = pysrt.open(temp_path, encoding='utf-8')
        
        target_lang = dest_lang.upper()
        if target_lang == 'EN': target_lang = 'EN-US'
        if target_lang == 'ZH-CN': target_lang = 'ZH'
        
        texts = [sub.text for sub in subs]
        results = translator.translate_text(texts, target_lang=target_lang)
        
        for i, sub in enumerate(subs):
            sub.text = results[i].text

        output = subs.serialise()
        nl = '\r\n' if newline_type == 'crlf' else '\n'
        output = output.replace('\r\n', '\n').replace('\n', nl)

        os.remove(temp_path)
        return Response(output, mimetype="text/plain", headers={"Content-Disposition": f"attachment; filename=translated_{dest_lang}.srt"})
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return str(e), 500

if __name__ == "__main__":
    # Render 포트 오류 해결의 핵심
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)