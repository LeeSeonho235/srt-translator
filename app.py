import os
import base64
import requests
import pysrt
import deepl
from datetime import datetime, timedelta
from flask import Flask, render_template, request, Response, redirect, url_for
from dotenv import load_dotenv
from supabase import create_client, Client

app = Flask(__name__)

# .env 파일 로드
load_dotenv()
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")

PORTONE_API_SECRET = os.getenv("PORTONE_API_SECRET")

# Supabase 설정
SUPABASE_URL              = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY         = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase_client: Client   = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL else None
supabase_admin:  Client   = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY) else None


def get_common_vars(**kwargs):
    kwargs['SUPABASE_URL'] = os.getenv("SUPABASE_URL", "")
    kwargs['SUPABASE_ANON_KEY'] = os.getenv("SUPABASE_ANON_KEY", "")
    return kwargs


@app.route("/")
def index():
    return render_template("index.html", **get_common_vars(view="main"))


# app.py /pricing 라우트
@app.route("/pricing")
def pricing():
    return render_template(
        "index.html",
        **get_common_vars(
            view="pricing",
            PORTONE_STORE_ID=os.getenv("PORTONE_STORE_ID"),
            PORTONE_CHANNEL_KEY_KAKAO=os.getenv("PORTONE_CHANNEL_KEY_KAKAO"),
            PORTONE_CHANNEL_KEY_PAYPAL=os.getenv("PORTONE_CHANNEL_KEY_PAYPAL")
        )
    )


# ── 환불 규정 페이지 ──────────────────────────────────────────────────────────
@app.route("/preview")
def preview():
    return render_template("preview.html")


@app.route("/refund")
def refund():
    return redirect(url_for('pricing'))


@app.route('/success')
def success():
    plan = request.args.get('plan')
    payment_id = request.args.get('paymentId')
    url_email = request.args.get('email')

    res = requests.get(
        f"https://api.portone.io/payments/{payment_id}",
        headers={"Authorization": f"PortOne {PORTONE_API_SECRET}"}
    )
    payment = res.json()

    print("=== PAYMENT STATUS ===", payment.get('status'))

    if payment.get('status') != 'PAID':
        return render_template('index.html', view='fail')

    user_email = payment.get('customer', {}).get('email') or url_email

    if plan == 'week':
        expires_at = datetime.utcnow() + timedelta(weeks=1)
    elif plan == 'month':
        expires_at = datetime.utcnow() + timedelta(days=30)
    elif plan == 'annual':
        expires_at = datetime.utcnow() + timedelta(days=365)
    else:
        expires_at = datetime.utcnow() + timedelta(days=365)

    if supabase_admin and user_email:
        supabase_admin.table('user_plans').upsert({
            'email': user_email,
            'plan_type': plan,
            'plan_expires_at': expires_at.isoformat()
        }, on_conflict='email').execute()

    return render_template('index.html', **get_common_vars(view='success', plan=plan, message='Payment completed successfully.'))
@app.route("/fail")
def payment_fail():
    return render_template("index.html", **get_common_vars(view='fail'))


@app.route('/api/my-plan')
def my_plan():
    email = request.args.get('email')
    if not email or not supabase_admin:
        return {'plan': None}
    
    result = supabase_admin.table('user_plans').select('*').eq('email', email).execute()
    if result.data:
        plan = result.data[0]
        expires_str = plan['plan_expires_at']
        # timezone-aware 비교
        expires_at = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
        now = datetime.now(expires_at.tzinfo)
        if expires_at > now:
            return {'plan': plan['plan_type'], 'expires_at': expires_str}
    return {'plan': None}


@app.route("/translate", methods=["POST"])
def translate_srt():
    if 'file' not in request.files:
        return "파일이 없습니다.", 400

    uploaded_file = request.files["file"]
    src_lang      = request.form.get("src_lang", "auto")
    dest_lang     = request.form.get("dest_lang", "ko")
    newline_type  = request.form.get("newline_type", "crlf")

    if not DEEPL_AUTH_KEY:
        return "Error: DeepL API 키가 설정되지 않았습니다.", 500

    temp_path = "/tmp/temp_to_translate.srt"
    uploaded_file.save(temp_path)

    try:
        target_lang = dest_lang.upper()
        if target_lang == 'EN':    target_lang = 'EN-US'
        if target_lang == 'ZH-CN': target_lang = 'ZH'
        source_lang = src_lang.upper() if src_lang != 'auto' else None

        translator = deepl.Translator(DEEPL_AUTH_KEY)
        subs        = pysrt.open(temp_path, encoding='utf-8')
        texts       = [sub.text for sub in subs]

        # 문맥 포함 번역: 앞뒤 자막 합쳐서 보내고 결과만 추출
        CONTEXT_WINDOW = 2  # 앞뒤 N개 자막을 문맥으로 활용
        translated_texts = []

        # 짧거나 의성어/감탄사처럼 보이는 텍스트 처리
        def is_skip_text(t):
            t = t.strip()
            # 특수문자만, 숫자만, 1글자 자음/모음, 괄호 안 지문 등
            import re
            if re.match(r'^[\(\[（【].*[\)\]）】]$', t): return False  # 괄호 지문은 번역
            if len(t) <= 1: return True  # 1글자 단독
            return False

        # 배치 번역 (문맥 포함)
        batch_texts = []
        batch_indices = []
        skip_map = {}

        for i, text in enumerate(texts):
            if is_skip_text(text):
                skip_map[i] = text  # 의성어/짧은 텍스트는 그대로
            else:
                # 앞뒤 문맥 포함한 텍스트 생성
                context_parts = []
                for j in range(max(0, i-CONTEXT_WINDOW), min(len(texts), i+CONTEXT_WINDOW+1)):
                    if j == i:
                        context_parts.append(f"[[[{text}]]]")  # 번역 대상 표시
                    else:
                        context_parts.append(texts[j])
                batch_texts.append('\n'.join(context_parts))
                batch_indices.append(i)

        if batch_texts:
            import re as _re
            results = translator.translate_text(batch_texts, source_lang=source_lang, target_lang=target_lang)
            for idx, result in zip(batch_indices, results):
                translated = result.text
                # [[[...]]] 사이의 번역된 텍스트만 추출
                match = _re.search(r'\[\[\[(.*?)\]\]\]', translated, _re.DOTALL)
                if match:
                    translated_texts_map = getattr(translated_texts, '_map', {})
                    skip_map[idx] = match.group(1).strip()
                else:
                    # 매칭 실패시 전체 결과 사용
                    skip_map[idx] = translated.strip()

        # 순서대로 자막에 적용
        for i, sub in enumerate(subs):
            sub.text = skip_map.get(i, texts[i])

        output_temp = "/tmp/output_temp.srt"
        subs.save(output_temp, encoding='utf-8')

        with open(output_temp, 'r', encoding='utf-8') as f:
            translated_srt = f.read()

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)