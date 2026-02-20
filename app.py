import os
import pysrt
import deepl
from flask import Flask, render_template, request
from dotenv import load_dotenv

app = Flask(__name__)

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY")

# 바탕화면 경로 설정
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

@app.route('/')
def index():
    supported_languages = [
        'ko', 'en', 'es', 'ja', 'zh-cn', 'vi', 
        'th', 'de', 'fr', 'it', 'pt', 'ru'
    ]
    lang = request.accept_languages.best_match(supported_languages)
    if not lang:
        lang = 'en'
    return render_template('index.html', user_lang=lang)

@app.route('/translate', methods=['POST'])
def translate():
    if 'file' not in request.files:
        return "파일이 없습니다.", 400
    
    file = request.files['file']
    src_lang_input = request.form.get('src_lang', 'auto')
    dest_lang_input = request.form.get('dest_lang', 'ko')
    # 사용자가 선택한 줄 바꿈 방식 (crlf 또는 lf)
    newline_type = request.form.get('newline_type', 'crlf')

    if file.filename == '':
        return "선택된 파일이 없습니다.", 400

    temp_path = "temp.srt"
    file.save(temp_path)

    try:
        # DeepL 언어 코드 매핑
        target_lang = dest_lang_input.upper()
        if target_lang == 'EN': target_lang = 'EN-US'
        if target_lang == 'ZH-CN': target_lang = 'ZH'
        
        source_lang = src_lang_input.upper() if src_lang_input != 'auto' else None

        translator = deepl.Translator(DEEPL_AUTH_KEY)
        subs = pysrt.open(temp_path, encoding='utf-8')
        
        # 텍스트만 추출하여 번역 (형식 보존 옵션 추가)
        texts_to_translate = [sub.text for sub in subs]
        results = translator.translate_text(
            texts_to_translate, 
            source_lang=source_lang, 
            target_lang=target_lang,
            preserve_formatting=True # 줄 바꿈 등 서식 최대한 보존
        )
        
        for i, sub in enumerate(subs):
            sub.text = results[i].text

        # 저장 파일명 및 경로 설정
        output_filename = f"translated_{dest_lang_input}_{file.filename}"
        output_path = os.path.join(DESKTOP_PATH, output_filename)

        # 줄 바꿈 문자 설정 (Windows: \r\n, Mac: \n)
        nl = '\r\n' if newline_type == 'crlf' else '\n'
        
        # 명시적으로 줄 바꿈 형식을 지정하여 저장
        with open(output_path, 'w', encoding='utf-8', newline=nl) as f:
            f.write(subs.serialise())

        os.remove(temp_path)
        return f"Success! Saved on Desktop as '{output_filename}' ({newline_type.upper()})"

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return f"Error: {str(e)}"

if __name__ == '__main__':
    if not DEEPL_AUTH_KEY:
        print("⚠️ DEEPL_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
    app.run(debug=True, port=5001)