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
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")

# 토스페이먼츠 설정 (테스트: test_gsk_..., 실서비스: live_gsk_...)
TOSSPAYMENTS_SECRET_KEY = os.getenv("TOSSPAYMENTS_SECRET_KEY", "test_gsk_docs_OaPz8L5KdmQXkzRz3y47BMw6")
TOSSPAYMENTS_CLIENT_KEY = os.getenv("TOSSPAYMENTS_CLIENT_KEY", "test_ck_D5GePWvyJnrK0W0k8eX3lmeaxYG5")

# Supabase 설정 (Render 환경변수에 추가)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # 유저 metadata 업데이트용
# Supabase 클라이언트 초기화
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL else None
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY) else None

@app.route("/")
def index():
    return render_template("index.html", view="main")

@app.route("/pricing")
def pricing():
    client_key = TOSSPAYMENTS_CLIENT_KEY or "test_ck_D5GePWvyJnrK0W0k8eX3lmeaxYG5"
    return render_template("index.html", view="pricing", TOSSPAYMENTS_CLIENT_KEY=client_key)

@app.route("/success")
def payment_success():
    payment_key = request.args.get("paymentKey")
    order_id = request.args.get("orderId")
    amount = request.args.get("amount")
    plan = request.args.get("plan", "week")  # week 또는 month

    if not all([payment_key, order_id, amount]):
        return "결제 정보가 올바르지 않습니다.", 400

    # 결제 금액 검증 (클라이언트 조작 방지)
    amount_int = int(amount)
    if plan == "week" and amount_int != 5000:
        return "결제 금액이 일치하지 않습니다.", 400
    if plan == "month" and amount_int != 10000:
        return "결제 금액이 일치하지 않습니다.", 400

    # 토스페이먼츠 승인 API 호출
    user_pass = TOSSPAYMENTS_SECRET_KEY + ":"
    encoded_u_p = base64.b64encode(user_pass.encode()).decode()

    url = "https://api.tosspayments.com/v1/payments/confirm"
    headers = {
        "Authorization": f"Basic {encoded_u_p}",
        "Content-Type": "application/json"
    }
    payload = {
        "paymentKey": payment_key,
        "orderId": order_id,
        "amount": amount_int
    }

    res = requests.post(url, json=payload, headers=headers)

    if res.status_code == 200:
        # TODO: 여기서 유저 권한 업데이트 로직 구현
        # 예: Supabase auth.users metadata에 is_paid=True, plan_type=plan, valid_until=날짜 등 저장
        # supabase_admin.auth.admin.update_user_by_id(user_id, {"user_metadata": {"is_paid": True, "plan_type": plan}})
        # 주의: 사용자 식별을 위해 successUrl에 user_id를 쿼리로 넘기거나, 세션/쿠키를 사용해야 함
        return render_template("index.html", view="success", message="결제가 완료되었습니다!", plan=plan)
    else:
        error_body = res.text
        return f"결제 승인 실패: {error_body}", 400

@app.route("/fail")
def payment_fail():
    return render_template("index.html", view="fail")

@app.route("/translate", methods=["POST"])
def translate_srt():
    if 'file' not in request.files:
        return "파일이 없습니다.", 400
    
    uploaded_file = request.files["file"]
    src_lang = request.form.get("src_lang", "auto")
    dest_lang = request.form.get("dest_lang", "ko")
    newline_type = request.form.get("newline_type", "crlf")

    if not DEEPL_AUTH_KEY:
        return "Error: DeepL API 키가 설정되지 않았습니다.", 500

    temp_path = "temp_to_translate.srt"
    uploaded_file.save(temp_path)

    try:
        # DeepL 언어 코드 처리
        target_lang = dest_lang.upper()
        if target_lang == 'EN': target_lang = 'EN-US'
        if target_lang == 'ZH-CN': target_lang = 'ZH'
        source_lang = src_lang.upper() if src_lang != 'auto' else None

        translator = deepl.Translator(DEEPL_AUTH_KEY)
        subs = pysrt.open(temp_path, encoding='utf-8')
        
        # 일괄 번역
        texts = [sub.text for sub in subs]
        results = translator.translate_text(texts, source_lang=source_lang, target_lang=target_lang)
        
        for i, sub in enumerate(subs):
            sub.text = results[i].text

        output_temp = "output_temp.srt"
        subs.save(output_temp, encoding='utf-8')
        
        with open(output_temp, 'r', encoding='utf-8') as f:
            translated_srt = f.read()

        # 줄바꿈 처리
        nl = '\r\n' if newline_type == 'crlf' else '\n'
        translated_srt = translated_srt.replace('\r\n', '\n').replace('\n', nl)

        os.remove(temp_path)
        os.remove(output_temp)

        return Response(
            translated_srt,
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename=translated_{dest_lang}.srt"}
        )

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    # Render 환경변수 PORT가 있으면 사용하고, 없으면 5000번 사용
    port = int(os.environ.get("PORT", 5000))
    # host를 0.0.0.0으로 설정해야 외부 접속이 가능합니다.
    app.run(host="0.0.0.0", port=port)