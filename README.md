# CodeAlpha AI Internship — Project 1: Language Translation Tool (Polyglot)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0+-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-purple)
![Status](https://img.shields.io/badge/Status-Completed-success)

A modern, responsive, full-stack multilingual language translation tool built for the **CodeAlpha Artificial Intelligence Internship**. This tool translates text between 25+ global languages in real-time, features responsive design for desktop and mobile, and provides speech synthesis and clipboard integration.

---

## 📑 Table of Contents
1. [Overview & Features](#overview--features)
2. [Architecture & Project Structure](#architecture--project-structure)
3. [Translation Provider Analysis & Setup](#translation-provider-analysis--setup)
4. [Windows Setup & Run Instructions](#windows-setup--run-instructions)
5. [Automated Testing](#automated-testing)
6. [Git Repository Instructions](#git-repository-instructions)
7. [Internship Demonstration Video Script](#internship-demonstration-video-script)
8. [CodeAlpha Final Submission Checklist](#codealpha-final-submission-checklist)

---

## 🌟 Overview & Features

- **Real-Time Multilingual Translation**: Seamless translation between 25+ global languages (English, Spanish, French, German, Mandarin, Arabic, Japanese, and African languages including Yoruba, Hausa, Igbo, and Swahili).
- **Auto Language Detection**: Enter any foreign language and let the tool automatically detect the source language.
- **Language Swapping**: Quickly toggle between source and target languages with intelligent state synchronization.
- **Zero Credentials Exposed**: Translation operations are proxied through a secure Flask backend. No secret keys or credentials are ever exposed to the client-side JavaScript.
- **Resilient Error Handling**: Gracefully handles network outages, rate limits, character overages, and empty submissions with clear user feedback banners and toast notifications.
- **Audio Pronunciation (Text-to-Speech)**: Native Web Speech API integration allows users to listen to the pronunciation of translated text.
- **Copy & Clear Shortcuts**: One-click clipboard copy with visual feedback, instant textarea clearance, and `Ctrl + Enter` translation hotkey.
- **Aesthetic Glassmorphism UI**: Custom CSS design system with ambient background glows, responsive layouts for mobile and desktop, and zero heavy UI framework overhead.

---

## 🏗️ Architecture & Project Structure

The project follows clean separation of concerns and an application factory pattern:

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
│   └── test_translation.py     # Comprehensive automated unit & integration tests
│
├── venv/                        # Isolated Python virtual environment
├── .env                         # Local environment configuration (git-ignored)
├── .env.example                 # Template for environment configuration
├── .gitignore                   # Excludes virtual envs, caches, and secrets
├── app.py                       # Flask application factory, routing & error handlers
├── config.py                    # Environment settings and configuration parsing
├── translator_service.py        # Translation provider abstraction and business logic
├── requirements.txt             # Locked Python package dependencies
└── README.md                    # Project documentation and submission guide
```

---

## 🌐 Translation Provider Analysis & Setup

### Selected Provider: `deep-translator` (Google Engine)

For a student internship project, selecting a translation provider requires balancing **accessibility, cost, ease of evaluation, and reliability**.

| Feature | Details |
| :--- | :--- |
| **Provider** | `deep-translator` using Google Translate web endpoint |
| **API Key Required?** | **No** — Works out-of-the-box without sign-up, billing, or credit card requirements |
| **Cost** | **100% Free** |
| **Character Limit** | 5,000 characters per single translation request (enforced on both client and server) |
| **Language Support** | Over 100 languages supported |
| **Setup Barrier** | Zero setup barrier for CodeAlpha evaluators and supervisors |
| **Rate Limit** | Free tier: ~5 requests/second, 200k/day. If you see a rate-limit message in the UI, wait 3–5 seconds and translate again. |

### Alternative Providers Supported
The backend abstraction (`translator_service.py`) is modular. You can easily switch providers via the `.env` configuration file:
- `TRANSLATION_PROVIDER=google` (Default, free)
- `TRANSLATION_PROVIDER=mymemory` (Alternative free provider, optional email for higher quota)

---

## 💻 Windows Setup & Run Instructions

Follow these exact steps in **PowerShell** or **Visual Studio Code Terminal** on Windows:

### Step 1: Open Terminal in the Project Directory
```powershell
cd c:\Users\Py-Craft\Desktop\Alameen\CODEALPHA\CodeAlpha_LanguageTranslation
```

### Step 2: Create a Virtual Environment (if not already created)
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
- **In PowerShell**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If PowerShell displays a script execution policy error, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*
- **In Command Prompt (cmd.exe)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables
Copy `.env.example` to `.env` (already done by default in this workspace):
```powershell
Copy-Item .env.example .env
```

### Step 6: Start the Flask Application
```powershell
python app.py
```

### Step 7: Access the Web Application
Open your web browser and navigate to:
```
http://127.0.0.1:8080
```

> **Note on Port 5000**: Windows may block port 5000 due to system access restrictions (e.g., AirPlay Receiver on some builds). The app uses port **8080** by default.

---

## 🧪 Automated Testing

Automated tests verify that routes, input validation, edge cases, and provider failure states are properly handled. External API calls are mocked using `pytest` and `unittest.mock` to ensure fast, deterministic tests that do not rely on live internet requests.

### Run the Tests
With the virtual environment activated, run:
```powershell
pytest -v
```

### Test Coverage Highlights:
- `test_home_page_renders`: Confirms the web UI loads with status `200 OK`.
- `test_api_languages_endpoint`: Confirms the languages list endpoint returns valid JSON.
- `test_health_check_endpoint`: Confirms the `/api/health` monitoring route functions.
- `test_translate_valid_request_with_mock`: Validates end-to-end translation pipeline.
- `test_translate_identical_languages_shortcut`: Ensures identical source and target bypass network calls.
- `test_translate_empty_text`: Asserts `400 Bad Request` on empty text submissions.
- `test_translate_target_cannot_be_auto`: Rejects `target_lang="auto"` with `400 Bad Request`.
- `test_translate_unsupported_language`: Rejects unknown language codes.
- `test_translate_char_limit_exceeded`: Rejects inputs exceeding maximum character limits.
- `test_translate_provider_network_failure`: Asserts `503 Service Unavailable` on network failure.
- `test_translate_provider_generic_error`: Asserts `502 Bad Gateway` on unexpected provider crashes.
- `test_translate_provider_empty_response`: Asserts `502 Bad Gateway` if provider returns `None`.

---

## 📦 Git Repository Instructions

To upload your project to GitHub for CodeAlpha review:

1. **Initialize Git** in the project directory:
   ```powershell
   git init
   ```
2. **Review tracked files** (verify `venv` and `.env` are ignored):
   ```powershell
   git status
   ```
3. **Stage all files**:
   ```powershell
   git add .
   ```
4. **Commit with a professional message**:
   ```powershell
   git commit -m "feat: complete CodeAlpha language translation tool project"
   ```
5. **Create a new public repository** on GitHub named `CodeAlpha_LanguageTranslation`.
6. **Link your remote repository and push**:
   ```powershell
   git branch -M main
   git remote add origin https://github.com/<your-username>/CodeAlpha_LanguageTranslation.git
   git push -u origin main
   ```

---

## 🎥 Internship Demonstration Video Script

When recording your 1–2 minute project demonstration video (e.g., using OBS Studio, Loom, or Windows Xbox Game Bar `Win + G`):

1. **Introduction (15 sec)**:
   - State your name and internship role: *"Hello, I am Alameen, Artificial Intelligence Intern at CodeAlpha. Today I am presenting Project 1: Language Translation Tool."*
2. **Architecture & Tech Stack (20 sec)**:
   - Briefly show VS Code: explain that it uses Python 3.12, Flask for the backend API, `deep-translator` for real-time translation, and a responsive frontend with vanilla CSS and JavaScript.
3. **Live Demonstration (45 sec)**:
   - Open browser at `http://127.0.0.1:5000`.
   - Type an English sentence (e.g., *"Artificial intelligence is transforming how people communicate across borders."*).
   - Select Spanish (`es`) and click **Translate** (or press `Ctrl + Enter`).
   - Show the translated result: click **Listen** to demonstrate audio pronunciation, then click **Copy** to demonstrate clipboard copying.
   - Demonstrate language swap and translate into French or Yoruba.
   - Test edge cases: show validation when clearing input or attempting empty submissions.
4. **Automated Testing (20 sec)**:
   - Switch back to terminal and run `pytest -v` to showcase all passing automated tests.
5. **Conclusion (10 sec)**:
   - Thank CodeAlpha for the assignment and close the video.

---

## ✅ CodeAlpha Final Submission Checklist

- [x] Project folder organized as `CodeAlpha_LanguageTranslation`.
- [x] Isolated Python virtual environment configured (`venv`).
- [x] Real translation provider integrated via `deep-translator`.
- [x] Responsive web interface supporting desktop and mobile.
- [x] Copy to clipboard and clear text functionality implemented.
- [x] Audio speech pronunciation implemented.
- [x] Graceful error feedback for empty input, network errors, and invalid codes.
- [x] Zero API credentials committed or exposed to the frontend.
- [x] `requirements.txt`, `.gitignore`, and `.env.example` created.
- [x] 100% automated test coverage with mocked external calls passing.
- [x] Submission-ready documentation and README completed.
