import os
import base64
import requests
import pysrt
import deepl
from flask import Flask, render_template, request, Response, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client

app = Flask(__name__)

# .env 파일 로드
load_dotenv()

# API 키 설정 (환경 변수 우선, 없으면 테스트 키 사용)
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")
TOSSPAYMENTS_CLIENT_KEY = os.getenv("TOSSPAYMENTS_CLIENT_KEY") or "test_ck_D5GePWvyJnrK0W0k8eX3lmeaxYG5"
TOSSPAYMENTS_SECRET_KEY = os.getenv("TOSSPAYMENTS_SECRET_KEY") or "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6"

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Supabase 클라이언트 초기화
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL else None
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY) else None

@app.route("/")
def index():
    return render_template("index.html", view="main")

@app.route("/pricing")
def pricing():
    # 클라이언트 키를 템플릿으로 전달 (이게 틀리면 인증 에러 발생)
    return render_template("index.html", view="pricing", TOSSPAYMENTS_CLIENT_KEY=TOSSPAYMENTS_CLIENT_KEY)

@app.route("/success")
def payment_success():
    payment_key = request.args.get("paymentKey")
    order_id = request.args.get("orderId")
    amount = request.args.get("amount")
    plan = request.args.get("plan", "week")

    if not all([payment_key, order_id, amount]):
        return "결제 정보가 올바르지 않습니다.", 400

    # 토스페이먼츠 승인 API 호출을 위한 인증 헤더
    user_pass = TOSSPAYMENTS_SECRET_KEY + ":"
    encoded_u_p = base64.b64encode(user_pass.encode()).decode()

    url = "https://api.tosspayments.com/v1/payments/confirm"
    headers = {
        "Authorization": f"Basic {encoded_u_p}",
        "Content-Type": "application/json"
    }
    
    res = requests.post(url, json={
        "paymentKey": payment_key,
        "orderId": order_id,
        "amount": int(amount)
    }, headers=headers)

    if res.status_code == 200:
        # 결제 성공 시 로직 (DB 업데이트 등)
        return render_template("index.html", view="success", message="결제가 완료되었습니다!", plan=plan)
    else:
        return f"결제 승인 실패: {res.text}", 400

@app.route("/fail")
def payment_fail():
    return render_template("index.html", view="fail")

@app.route("/translate", methods=["POST"])
def translate_srt():
    if 'file' not in request.files: return "No file", 400
    
    file = request.files["file"]
    src_lang = request.form.get("src_lang", "auto")
    dest_lang = request.form.get("dest_lang", "ko")
    newline_type = request.form.get("newline_type", "crlf")

    if not DEEPL_AUTH_KEY: return "DeepL Key Missing", 500

    temp_path = "temp.srt"
    file.save(temp_path)

    try:
        translator = deepl.Translator(DEEPL_AUTH_KEY)
        subs = pysrt.open(temp_path, encoding='utf-8')
        
        target = dest_lang.upper()
        if target == 'EN': target = 'EN-US'
        if target == 'ZH-CN': target = 'ZH'
        
        texts = [sub.text for sub in subs]
        results = translator.translate_text(texts, target_lang=target)
        
        for i, sub in enumerate(subs):
            sub.text = results[i].text

        output = subs.serialise()
        nl = '\r\n' if newline_type == 'crlf' else '\n'
        output = output.replace('\r\n', '\n').replace('\n', nl)

        os.remove(temp_path)
        return Response(output, mimetype="text/plain", headers={"Content-Disposition": f"attachment; filename=translated.srt"})
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)