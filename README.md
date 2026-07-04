# K-Name Generator

> **AI-powered Korean name generator for foreigners** — Get a meaningful Korean name with Hanja characters and a custom AI-generated portrait card.

![Status](https://img.shields.io/badge/status-archived-yellow)
![Commits](https://img.shields.io/badge/commits-104+-blue)
![Python](https://img.shields.io/badge/python-FastAPI-green)
![AI](https://img.shields.io/badge/AI-Gemini%20%2B%20DALL--E-purple)

<img width="501" height="556" alt="스크린샷 2026-07-04 17 00 09" src="https://github.com/user-attachments/assets/627a0e5c-2fb5-499b-ae9e-cd073c73305d" />
<img width="504" height="557" alt="스크린샷 2026-07-04 17 00 00" src="https://github.com/user-attachments/assets/a5b77c34-f000-4e0b-9c99-f9c30a477b74" />

## What It Does

K-Name Generator creates personalized Korean names for foreigners based on their English name, gender, and personality. Users receive:

- A **Korean name** (한글) with **Hanja** (漢字) characters or pure Korean (순우리말) names
- The **meaning** of each character explained in their language
- An **AI-generated portrait card** in traditional Korean hanbok style
- A **flippable card UI** — front shows the portrait, back shows the Hanja breakdown

## Supported Languages

English · Spanish · Chinese · Japanese · Korean

## Name Generation Styles

| Style | Description |
|-------|-------------|
| **Sound** | Korean name that sounds phonetically similar to your English name |
| **Meaning** | Korean name with Hanja characters matching your personality |
| **K-Drama** | Korean name inspired by K-Drama character naming conventions |

## Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python, FastAPI |
| **AI — Name Generation** | Google Gemini 2.0 Flash |
| **AI — Portrait Generation** | OpenAI DALL-E 3 |
| **Authentication** | Supabase (Google OAuth) |
| **Payment** | PortOne (PayPal) |
| **Analytics** | Google Analytics, Google AdSense |
| **Deployment** | Railway |
| **Frontend** | HTML, CSS, JavaScript (Vanilla) |

## Architecture

```
User Input (Name, Gender, Vibe, Style, Language)
        │
        ▼
   FastAPI Server
        │
        ├──▶ Gemini 2.0 Flash ──▶ Generate Korean Name + Hanja + Meaning
        │
        ├──▶ DALL-E 3 ──▶ Generate Hanbok Portrait Card
        │         │
        │         └──▶ Image Proxy ──▶ Serve to Frontend (CORS-safe)
        │
        ├──▶ Supabase ──▶ Google OAuth + Subscription Management
        │
        └──▶ PortOne ──▶ PayPal Payment (Weekly / Monthly / Annual Plans)
        │
        ▼
   Flippable Name Card
   Front: AI Hanbok Portrait + Korean Name
   Back: Hanja Breakdown + Character Meanings
```

## Key Features

- ulti-language UI: Supports 5 languages (EN, ES, ZH, JA, KO)
- ual Name Types: Hanja-based names (漢字) and pure Korean names (순우리말)
- AI Portrait Generation** — DALL-E 3 creates a unique Korean-style watercolor portrait for each name
- Flippable Card UI:Interactive card revealing name details on tap/click
- Subscription Plans: Weekly, monthly, and annual plans via PortOne + PayPal
- Image Proxy: Server-side proxy for DALL-E images to handle CORS
- SEO Optimized: Sitemap, robots.txt, and Google AdSense integration

## Screenshots

> *Add screenshots here after uploading to the repository*

## Getting Started

### Prerequisites
- Python 3.9+
- Google Gemini API Key
- OpenAI API Key (DALL-E 3)
- Supabase Project (URL + Service Role Key + Anon Key)
- PortOne Account (Store ID + Channel Keys)

### Installation

```bash
# Clone the repository
git clone https://github.com/LeeSeonho235/k-identity.git
cd k-identity

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
SUPABASE_URL=your_url
SUPABASE_SERVICE_ROLE_KEY=your_key
SUPABASE_ANON_KEY=your_key
PORTONE_API_SECRET=your_secret
PORTONE_STORE_ID=your_store_id
PORTONE_CHANNEL_KEY_KAKAO=your_key
PORTONE_CHANNEL_KEY_PAYPAL=your_key
EOF

# Run the server
uvicorn main:app --reload
```

## What I Learned

- Integrating multiple AI APIs (Gemini 2.0 Flash + DALL-E 3) into a single generation pipeline
- Building a server-side image proxy to handle third-party API CORS restrictions
- Implementing subscription-based payment with PortOne (PayPal integration)
- Designing regex-based post-processing for structured AI output (Hanja parsing)
- Managing user authentication and subscription state with Supabase
- SEO optimization for a consumer-facing web service (sitemap, robots.txt, AdSense)

## Note

This service was previously live at **knamegenerator.com** but has been archived. The source code remains available for reference.

## License

MIT License
