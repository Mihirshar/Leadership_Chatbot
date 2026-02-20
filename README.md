# EXL Leadership AI — Gamified Avatar Platform

An interactive Streamlit application for the **EXL AI Summit 2026**. Visitors choose a leadership avatar, ask questions, and get personality-driven responses — complete with AI-generated avatars, cloned voices, and lip-sync videos.

## ✨ Key Features

- **3 Leadership Avatars** — Vikram, Anil, and Ishraq, each with distinct personalities, speech patterns, and values built from YAML configs.
- **AI Avatar Booth** — Visitors snap a photo and Gemini creates a stylized, futuristic avatar on the spot.
- **Voice Cloning (ElevenLabs)** — Leaders respond with their actual cloned voices for hyper-realism.
- **Lip-Sync Video (Fal.ai)** — Avatars speak with perfect lip synchronization using the `sadtalker` model.
- **Gamification** — Users earn XP, level up from "Observer" to "Oracle", and unlock badges.
- **Scenario Library** — Pre-built leadership scenarios to jumpstart conversations.
- **Dynamic UI** — Cinematic animations, floating orbs, and a "living" interface that reacts to the conversation.

## 📂 Project Structure

```
Clawdbot/
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .streamlit/
│   ├── config.toml               # Streamlit theme & server config
│   └── secrets.toml              # API keys (local dev - DO NOT COMMIT)
│
├── core/
│   ├── llm_client.py             # Google Gemini 2.5 Flash — intelligence & responses
│   ├── voice_client.py           # TTS & Video: ElevenLabs + Fal.ai + Edge TTS fallback
│   ├── avatar_generator.py       # AI avatar generation (Gemini Image / Pillow)
│   ├── prompt_builder.py         # System prompt engineering
│   └── personality_engine.py     # Leader config loader & gamification logic
│
├── components/
│   ├── avatar_card.py            # Avatar/Video rendering & animations
│   ├── chat_ui.py                # Chat interface & bubbles
│   └── leaderboard.py            # XP panel & badge system
│
├── config/
│   └── leaders/                  # Personality definitions (YAML)
│       ├── vikram.yaml
│       ├── anil.yaml
│       └── ishraq.yaml
│
├── assets/
│   ├── leaders/                  # Leader-specific assets
│   │   ├── anil/                 #   ├── avatar.png
│   │   ├── vikram/               #   └── source.png
│   │   └── ishraq/
│   ├── visitors/                 # Generated user avatars saved here
│   ├── ui/                       # Logos, favicons, background assets
│   └── voices/                   # (Optional) MP3 samples for voice cloning
│
└── docs/
    └── leadership_personality_questionnaire.md
```

## 🚀 Prerequisites

- **Python 3.10+**
- **Google API Key** — for Gemini 2.5 Flash (Intelligence + Avatar Gen)
- **ElevenLabs API Key** — for Voice Cloning (Text-to-Speech)
- **Fal.ai Key** — for Lip-Sync Video Generation

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Clawdbot
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🔑 Configuration & Secrets

You must provide API keys for the app to function fully.

### Option 1: Secrets File (Recommended)
Create a file named `.streamlit/secrets.toml` in the root directory:

```toml
# Required: Intelligence & Avatar Generation
GOOGLE_API_KEY = "your_google_api_key"

# Required: Voice Cloning (ElevenLabs)
ELEVENLABS_API_KEY = "your_elevenlabs_key"

# Required: Lip-Sync Video (Fal.ai)
FAL_KEY = "your_fal_key"
```

### Option 2: Environment Variables
You can also set these in your terminal before running the app (see "Running the App" below).

## ▶️ Running the App

### Standard Run (using secrets.toml)
```bash
streamlit run app.py
```

### Run with Environment Variables (PowerShell)
If you don't want to create a secrets file, run this single command line:

```powershell
$env:GOOGLE_API_KEY="your_key"; $env:ELEVENLABS_API_KEY="your_key"; $env:FAL_KEY="your_key"; streamlit run app.py
```

### Run with Environment Variables (Mac/Linux)
```bash
export GOOGLE_API_KEY="your_key"
export ELEVENLABS_API_KEY="your_key"
export FAL_KEY="your_key"
streamlit run app.py
```

The app will open at **http://localhost:8501**.

## 🧠 How It Works

### 1. Voice & Video Pipeline
The app automatically selects the best available method:

| Feature | Service | Fallback |
|---------|---------|----------|
| **Voice** | **ElevenLabs** (Cloned) | Edge TTS (Free Neural) → Browser TTS |
| **Video** | **Fal.ai** (SadTalker) | Static Avatar Image |

### 2. Gamification System
- **XP**: Earn 50 XP per question.
- **Levels**: Observer → Apprentice → Strategist → Advisor → Visionary → Oracle.
- **Badges**: Unlocked by asking questions (Curious Mind, Deep Thinker) or talking to multiple leaders (Explorer, Champion).

## ➕ Adding New Leaders

1. Create a new YAML file in `config/leaders/` (e.g., `new_leader.yaml`).
2. Create a folder `assets/leaders/new_leader/`.
3. Add their **avatar.png** and **source.png** to that folder.
4. Update the YAML to point to these files and set their `voice_id` (ElevenLabs ID).

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| **App won't start** | Ensure you're in the `Clawdbot` directory and `venv` is active. |
| **"Module not found"** | Run `pip install -r requirements.txt` again. |
| **Video not playing** | Fal.ai generation might be pending or failed. Check console logs. |
| **Voice is robotic** | Check `ELEVENLABS_API_KEY`. If missing, it falls back to Edge TTS. |
| **Avatar gen fails** | Check `GOOGLE_API_KEY` quota. It falls back to a filter-based generator. |

## 📄 License
Internal — **EXL AI Summit 2026**.
