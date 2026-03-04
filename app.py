import os
import pysrt
import deepl
import requests
import base64
from flask import Flask, render_template, request, Response, stream_with_context
from dotenv import load_dotenv

app = Flask(__name__)

# 환경 변수 로드
load_dotenv()
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

# 토스페이먼츠 결제 성공 처리
@app.route("/success")
def payment_success():
    payment_key = request.args.get("paymentKey")
    order_id = request.args.get("orderId")
    amount = request.args.get("amount")

    # 토스 시크릿 키 (테스트용)
    secret_key = "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"
    user_pass = secret_key + ":"
    encoded_u_p = base64.b64encode(user_pass.encode()).decode()

    url = "https://api.tosspayments.com/v1/payments/confirm"
    headers = {
        "Authorization": f"Basic {encoded_u_p}",
        "Content-Type": "application/json"
    }
    
    res = requests.post(url, json={
        "paymentKey": payment_key,
        "orderId": order_id,
        "amount": amount
    }, headers=headers)

    if res.status_code == 200:
        # 결제 성공 시 메시지와 함께 메인으로 리다이렉트 (실제 서비스 시 DB 업데이트 필수)
        return render_template("index.html", payment_msg="Success! Your plan is activated.")
    else:
        return "Payment Confirmation Failed", 400

@app.route("/fail")
def payment_fail():
    return render_template("index.html", payment_msg="Payment Failed. Please try again.")

@app.route("/translate", methods=["POST"])
def translate_srt():
    if not DEEPL_AUTH_KEY:
        return "DeepL API Key missing", 500

    file = request.files.get("file")
    src_lang = request.form.get("src_lang", "EN")
    dest_lang = request.form.get("dest_lang", "KO")
    newline_type = request.form.get("newline_type", "crlf")

    if not file:
        return "No file uploaded", 400

    temp_path = "temp.srt"
    file.save(temp_path)

    try:
        subs = pysrt.open(temp_path, encoding='utf-8')
    except:
        subs = pysrt.open(temp_path, encoding='cp949')

    translator = deepl.Translator(DEEPL_AUTH_KEY)

    def generate():
        output = []
        for sub in subs:
            translated = translator.translate_text(sub.text, source_lang=src_lang.upper(), target_lang=dest_lang.upper())
            sub.text = translated.text
            
            line = f"{sub.index}\n{sub.start} --> {sub.end}\n{sub.text}\n\n"
            if newline_type == "crlf":
                line = line.replace("\n", "\r\n")
            output.append(line)
        
        os.remove(temp_path)
        yield "".join(output)

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename=translated_{dest_lang}.srt"}
    )

if __name__ == "__main__":
    # Render 포트 대응
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)