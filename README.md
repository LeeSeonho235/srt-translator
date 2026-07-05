# SRT Translator

Online SRT subtitle translator powered by DeepL. Upload an SRT file, pick the target language, and download the translated version. Also includes a free SRT subtitle viewer with video sync.

> Previously live at **srt-translator.com** (now archived)

<img width="1435" height="723" alt="스크린샷 2026-07-05 17 26 26" src="https://github.com/user-attachments/assets/02cc9caa-cc59-4537-b5ed-b8b74b297cb4" />
<img width="608" height="701" alt="스크린샷 2026-07-05 17 24 13" src="https://github.com/user-attachments/assets/8248088b-8f65-406f-8eca-a6727f64f0ac" />

## What It Does

**Translator** — Upload any `.srt` subtitle file and translate it into 20+ languages using DeepL. The translation uses a context window (surrounding subtitles) so each line is translated with awareness of what comes before and after, which avoids the common issue of subtitles being translated in isolation.

**SRT Viewer** — A free built-in subtitle previewer. Load an `.srt` file alongside a video to see subtitles synced with playback. Includes search and click-to-seek.

<img width="1440" height="814" alt="스크린샷 2026-07-05 17 28 14" src="https://github.com/user-attachments/assets/2219cfdc-139f-4d9c-9677-c4840f7747e2" />


## How the Context Translation Works

Most subtitle translators send each line separately to the API, which produces awkward results. This app wraps each subtitle with its 2 neighboring lines as context, marked with `[[[target]]]`, then extracts only the translated target:

```
Line before              ← context
[[[Line to translate]]]  ← actual target
Line after               ← context
```

This gives DeepL enough context to handle pronouns, tone, and continuity across lines.

## Tech Stack

- **Backend:** Python, Flask
- **Translation:** DeepL API (context-aware batching)
- **SRT Parsing:** pysrt
- **Auth:** Supabase (Google OAuth)
- **Payment:** PortOne (PayPal)
- **Analytics:** Google Analytics, AdSense
- **Deployment:** Railway (Gunicorn)
- **Frontend:** HTML, Tailwind CSS, vanilla JS

## Pages

- `/` — Main translator page (upload, translate, download)
- `/preview` — Free SRT viewer with video sync
- `/pricing` — Subscription plans (weekly / monthly / annual)
- `/privacy` — Privacy policy

## Setup

```bash
git clone https://github.com/LeeSeonho235/srt-translator.git
cd srt-translator
pip install -r requirements.txt
```

Create a `.env` file:

```
DEEPL_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
SUPABASE_SERVICE_ROLE_KEY=your_key
PORTONE_API_SECRET=your_secret
PORTONE_STORE_ID=your_store_id
PORTONE_CHANNEL_KEY_PAYPAL=your_key
```

Run:

```bash
python app.py
```

## Things I Learned Building This

- Context-aware translation by batching subtitles with surrounding lines for better coherence
- SRT file parsing and reconstruction while preserving timestamps and formatting
- Building a subtitle viewer with video sync using the `timeupdate` event
- Handling CSP headers for third-party payment iframe compatibility (PayPal via PortOne)
- Content Security Policy tuning for multiple external scripts (Tailwind CDN, PayPal, Google Analytics)
- SEO for a tool-based site: structured data (JSON-LD), canonical URLs, sitemap

## License

MIT
