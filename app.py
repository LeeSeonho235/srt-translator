from flask import Flask, render_template, request, Response
import pysrt
from googletrans import Translator
import os
import tempfile

app = Flask(__name__)
translator = Translator()

@app.route("/")
def index():
    return render_template("index.html", user_lang="en")


@app.route("/translate", methods=["POST"])
def translate_srt():
    uploaded_file = request.files["file"]
    src_lang = request.form.get("src_lang")
    dest_lang = request.form.get("dest_lang")
    newline_type = request.form.get("newline_type")

    if not uploaded_file:
        return "No file uploaded", 400

    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_file:
        uploaded_file.save(temp_file.name)
        temp_path = temp_file.name

    # SRT 읽기
    subs = pysrt.open(temp_path, encoding="utf-8")

    # 자막 번역
    for sub in subs:
        if sub.text.strip():
            translated = translator.translate(
                sub.text,
                src=src_lang,
                dest=dest_lang
            )
            sub.text = translated.text

    # ❗ serialize() 대신 str(subs) 사용
    translated_srt = str(subs)

    # 줄바꿈 옵션 처리
    if newline_type == "crlf":
        translated_srt = translated_srt.replace("\n", "\r\n")

    # 임시파일 삭제
    os.remove(temp_path)

    return Response(
        translated_srt,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=translated.srt"
        }
    )


if __name__ == "__main__":
    app.run(debug=True)