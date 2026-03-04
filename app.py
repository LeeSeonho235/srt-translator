import os
import pysrt
import deepl
from flask import Flask, render_template, request, Response
from dotenv import load_dotenv
from supabase import create_client, Client

app = Flask(__name__)

# .env 파일 로드
load_dotenv()
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")

# Supabase 설정 (Render 환경변수에 추가)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# Supabase 클라이언트 초기화
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL else None

@app.route("/")
def index():
    return render_template("index.html")

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