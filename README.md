# CodeAlpha AI Internship — Project 1: Language Translation Tool (Polyglot)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?logo=flask)
![DeepL API](https://img.shields.io/badge/DeepL-Official_SDK-0F2B46?logo=deepl)
![License](https://img.shields.io/badge/License-MIT-purple)
![Status](https://img.shields.io/badge/Status-Completed-success)

A modern, responsive, full-stack multilingual language translation tool built for the **CodeAlpha Artificial Intelligence Internship**. This tool translates text between 30+ global languages in real-time powered by the **official DeepL Python SDK**, features responsive glassmorphism UI for desktop and mobile, speech synthesis, and zero-exposure credential handling.

---

## 📑 Table of Contents
1. [Overview & Features](#overview--features)
2. [DeepL API Integration & Setup](#deepl-api-integration--setup)
3. [Architecture & Project Structure](#architecture--project-structure)
4. [Windows Setup & Run Instructions](#windows-setup--run-instructions)
5. [Supported Languages & Limitations](#supported-languages--limitations)
6. [Automated Testing](#automated-testing)
7. [Flask REST API Contract](#flask-rest-api-contract)
8. [Git Security & Rollback Safeguards](#git-security--rollback-safeguards)

---

## 🌟 Overview & Features

- **Official DeepL API Integration**: Powered by the official `deepl` Python SDK (`deepl.DeepLClient`) for high-accuracy translation.
- **Automatic Language Detection**: DeepL automatically detects the source language when `source_lang="auto"` is selected.
- **Dialect & Language Mapping**: Intelligent mapping layer handles regional variants required by DeepL (e.g., `en` → `EN-US`, `pt` → `PT-PT`, `zh-CN` → `ZH`).
- **Zero Credentials Exposed**: API keys (`DEEPL_AUTH_KEY`) are kept in the git-ignored `.env` file and processed entirely on the Flask server.
- **Resilient Error Handling**: Clear HTTP status codes and user-friendly error banners for missing credentials (503), authentication failures (401), quota exhaustion (429), rate limits (429), and provider timeouts (503).
- **Audio Pronunciation (Text-to-Speech)**: Native Web Speech API integration to hear translations.
- **Glassmorphism Design**: Custom dark-mode glass UI with ambient background glow and responsive layout.

---

## 🔑 DeepL API Integration & Setup

### 1. Get a DeepL API Key
Sign up for a free or pro API account on the official DeepL developer portal:
👉 **[DeepL API Sign Up](https://www.deepl.com/pro-api)**

- **Free Tier Allowance**: 500,000 characters per month.
- **Authentication Key Format**: Free keys typically end in `:fx` (e.g. `12345678-abcd-1234-abcd-1234567890ab:fx`).

### 2. Configure `.env`
Copy `.env.example` to `.env` (or update your existing `.env` file):

```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev_secret_key_codealpha_2026
PORT=8080

TRANSLATION_PROVIDER=deepl
DEEPL_AUTH_KEY=your_actual_deepl_api_key_here
MAX_CHAR_LIMIT=5000
```

> ⚠️ **Important Security Note**: Never commit `.env` or your real `DEEPL_AUTH_KEY` to Git repositories. `.env` is git-ignored by default.

---

## 🏗️ Architecture & Project Structure

```text
CodeAlpha_LanguageTranslation/
│
├── static/
│   ├── css/
│   │   └── style.css            # Custom responsive glassmorphic stylesheet
│   └── js/
│       └── app.js               # Client-side async logic, TTS, and clipboard handlers
│
├── templates/
│   └── index.html               # Semantic HTML5 template rendered by Jinja2
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration and application fixtures
│   └── test_translation.py     # 20 unit & integration tests with DeepL mocks
│
├── venv/                        # Isolated Python virtual environment (git-ignored)
├── .env                         # Local environment configuration (git-ignored)
├── .env.example                 # Environment configuration template
├── .gitignore                   # Excludes .env, venv/, and cache files
├── app.py                       # Flask application factory and API routes
├── config.py                    # Environment settings loader
├── requirements.txt             # Project dependencies (Flask, deepl, pytest, etc.)
├── translator_service.py        # DeepLClient integration and language mapping service
└── README.md                    # Internship project documentation
```

---

## 🚀 Windows Setup & Run Instructions

### Step 1: Open PowerShell in Project Folder
```powershell
cd CodeAlpha_LanguageTranslation
```

### Step 2: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run Flask Server
```powershell
python app.py
```

Access the UI at: **`http://127.0.0.1:8080`**

---

## 🌐 Supported Languages & Limitations

### DeepL Supported Languages (30+ Global Languages)
| Code | Language | DeepL Target Code |
| :--- | :--- | :--- |
| `auto` | Auto-Detect | `None` |
| `en` | English | `EN-US` |
| `es` | Spanish | `ES` |
| `fr` | French | `FR` |
| `de` | German | `DE` |
| `it` | Italian | `IT` |
| `pt` | Portuguese | `PT-PT` |
| `ru` | Russian | `RU` |
| `zh-CN` | Chinese (Simplified) | `ZH` |
| `ja` | Japanese | `JA` |
| `ko` | Korean | `KO` |
| `ar` | Arabic | `AR` |
| `nl` | Dutch | `NL` |
| `pl` | Polish | `PL` |
| `sv` | Swedish | `SV` |
| `tr` | Turkish | `TR` |
| `uk` | Ukrainian | `UK` |
| `id` | Indonesian | `ID` |

### Provider Limitations
- **Unsupported Dialects**: Languages not supported by DeepL (such as Yoruba `yo`, Hausa `ha`, Igbo `ig`, Swahili `sw`) are automatically excluded from advertised options when `TRANSLATION_PROVIDER=deepl`.
- **Quota Limit**: Free tier is capped at 500k characters/month. When exceeded, the service returns HTTP 429 with a clear explanation.
- **Unconfigured Credentials**: If `DEEPL_AUTH_KEY` is omitted, the API returns HTTP 503 rather than returning fake or broken translations.

---

## 🧪 Automated Testing

The project includes a 20-test suite covering UI rendering, Flask API routes, parameter validation, DeepL SDK mocking, network failure isolation, authentication errors, quota limits, and language mapping.

### Run Unit Tests
```powershell
python -m pytest -v
```

### Test Output Summary
```text
============================= 20 passed in 3.39s ==============================
```

---

## 📡 Flask REST API Contract

### 1. Languages Endpoint
`GET /api/languages`

**Response (200 OK):**
```json
{
  "success": true,
  "languages": {
    "auto": "Detect Language",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German"
  }
}
```

### 2. Translation Endpoint
`POST /api/translate`

**Request Body:**
```json
{
  "text": "Hello, welcome to CodeAlpha!",
  "source_lang": "en",
  "target_lang": "fr"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "translated_text": "Bonjour, bienvenue sur CodeAlpha !",
  "source_lang": "en",
  "target_lang": "fr",
  "character_count": 28,
  "provider": "deepl"
}
```

**Error Response (e.g. Missing Key - 503 Service Unavailable):**
```json
{
  "success": false,
  "error": "DeepL API authentication key is missing. Please set DEEPL_AUTH_KEY in your .env file."
}
```

---

## 🛡️ Git Security & Rollback Safeguards

- `.env` and `venv/` are verified git-ignored.
- A baseline rollback commit (`928f4a9`) was created prior to the DeepL migration.
- No production deployment or remote Git push will be performed without supervisor/user authorization.
