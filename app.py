import os
import pysrt
import deepl
from flask import Flask, render_template, request
from dotenv import load_dotenv

app = Flask(__name__)

# .env 파일 로드
load_dotenv()

# 발급받은 키를 .env에 넣었거나 아래 따옴표 안에 직접 넣으세요
DEEPL_AUTH_KEY = os.getenv("DEEPL_API_KEY") or "fbac7963-c99c-484e-b867-e1d34dfd0495:fx"

# 바탕화면 경로
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")

@app.route('/')
def index():
    supported_languages = ['ko', 'en', 'es', 'ja', 'zh-cn', 'vi', 'th', 'de', 'fr', 'it', 'pt', 'ru']
    lang = request.accept_languages.best_match(supported_languages) or 'en'
    return render_template('index.html', user_lang=lang)

@app.route('/translate', methods=['POST'])
def translate():
    if 'file' not in request.files:
        return "파일이 없습니다.", 400
    
    file = request.files['file']
    src_lang_input = request.form.get('src_lang', 'auto')
    dest_lang_input = request.form.get('dest_lang', 'ko')
    newline_type = request.form.get('newline_type', 'crlf')

    if file.filename == '':
        return "선택된 파일이 없습니다.", 400

    temp_path = "temp.srt"
    file.save(temp_path)

    try:
        # 1. DeepL 언어 코드 변환
        target_lang = dest_lang_input.upper()
        if target_lang == 'EN': target_lang = 'EN-US'
        if target_lang == 'ZH-CN': target_lang = 'ZH'
        
        source_lang = src_lang_input.upper() if src_lang_input != 'auto' else None

        # 2. 번역 실행
        translator = deepl.Translator(DEEPL_AUTH_KEY)
        subs = pysrt.open(temp_path, encoding='utf-8')
        
        texts_to_translate = [sub.text for sub in subs]
        results = translator.translate_text(
            texts_to_translate, 
            source_lang=source_lang, 
            target_lang=target_lang,
            preserve_formatting=True
        )
        
        for i, sub in enumerate(subs):
            sub.text = results[i].text

        # 3. 저장 (철자 수정: serialize)
        output_filename = f"translated_{dest_lang_input}_{file.filename}"
        output_path = os.path.join(DESKTOP_PATH, output_filename)
        nl = '\r\n' if newline_type == 'crlf' else '\n'
        
        # 'serialize'로 철자를 수정했습니다!
        with open(output_path, 'w', encoding='utf-8', newline=nl) as f:
            f.write(subs.serialize())

        os.remove(temp_path)
        return f"성공! 바탕화면에서 '{output_filename}' 파일을 확인하세요."

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)