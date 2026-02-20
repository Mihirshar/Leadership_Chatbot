# EXL Leadership AI — Gamified Avatar Platform

An interactive Streamlit application for the **EXL AI Summit 2026**. Visitors choose a leadership avatar, ask questions, and get personality-driven responses — complete with AI-generated avatars, text-to-speech voices, and a gamified XP system.

## Features

- **3 Leadership Avatars** — each with distinct personality, speech patterns, and values built from YAML configs (Vikram, Anil, Ishraq)
- **AI Avatar Generation** — visitors snap a photo and Gemini creates a stylized avatar on the spot
- **Voice Output (TTS)** — leaders respond with audio using cloned voices (ElevenLabs) or free neural voices (Edge TTS)
- **Gamification** — XP points, leveling, and badges earned through conversations
- **Scenario Library** — pre-built leadership scenarios visitors can tap to start a conversation

## Project Structure

```
Clawdbot/
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .streamlit/
│   ├── config.toml               # Streamlit theme & server config
│   └── secrets.toml              # API keys (local dev - DO NOT COMMIT)
│
├── core/
│   ├── llm_client.py             # Google Gemini 2.5 Flash — leader responses
│   ├── voice_client.py           # TTS: ElevenLabs (cloned) → Edge TTS (free) → browser fallback
│   ├── avatar_generator.py       # AI avatar generation from photos
│   ├── prompt_builder.py         # Builds system prompts from leader YAML
│   └── personality_engine.py     # Loads leader configs, XP levels, badges
│
├── components/
│   ├── avatar_card.py            # Avatar rendering, TTS dialogue, animations
│   ├── chat_ui.py                # Chat message bubbles, welcome screen
│   └── leaderboard.py            # XP panel, badges, insight cards
│
├── utils/
│   └── helpers.py                # Image utils, scenarios, color helpers
│
├── config/
│   └── leaders/                  # One YAML per leader (personality, values, speech patterns)
│       ├── vikram.yaml
│       ├── anil.yaml
│       └── ishraq.yaml
│
├── assets/
│   ├── leaders/                  # Leader-specific assets
│   │   ├── anil/                 # e.g., avatar.png, source.png
│   │   ├── vikram/
│   │   └── ishraq/
│   ├── visitors/                 # Auto-generated visitor avatars
│   ├── ui/                       # Logo and UI assets
│   └── voices/                   # Voice samples for cloning
│
└── docs/
    └── leadership_personality_questionnaire.md
```

## Prerequisites

- **Python 3.11+**
- **Google API Key** — for Gemini 2.5 Flash (chat + avatar generation)
- **ElevenLabs API Key** *(optional)* — for cloned leader voices
- **Edge TTS** works out of the box with no API key (free Microsoft neural voices)

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd Clawdbot

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## Configuration & Secrets (API Keys)

You can provide API keys via a local secrets file or environment variables.

### Option 1: Local Secrets File (Recommended for Local Dev)
1. Create a file named `.streamlit/secrets.toml` in the project root.
2. Add your keys:
   ```toml
   GOOGLE_API_KEY = "your_google_api_key_here"
   ELEVENLABS_API_KEY = "your_elevenlabs_key_here"  # Optional
   ```
3. **Note:** This file is ignored by Git to keep your keys safe.

### Option 2: Streamlit Cloud (For Deployment)
1. Go to your app dashboard on Streamlit Cloud.
2. Click **Settings** > **Secrets**.
3. Paste the TOML content into the text area:
   ```toml
   GOOGLE_API_KEY = "your_google_api_key_here"
   ELEVENLABS_API_KEY = "your_elevenlabs_key_here"
   ```

### Option 3: Environment Variables
You can still set keys in your terminal session if you prefer:
- Windows (PowerShell): `$env:GOOGLE_API_KEY="your-key"`
- Mac/Linux: `export GOOGLE_API_KEY="your-key"`

## Running the App

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**.

## Voice System — How It Works

The app uses a 3-tier TTS priority chain. No configuration needed — it picks the best available option automatically:

| Tier | Engine | Cost | Voice Quality | Setup |
|------|--------|------|---------------|-------|
| 1 | **ElevenLabs** | ~$99/mo (Pro) | Cloned from real voice samples | Set `ELEVENLABS_API_KEY` + drop MP3 samples in `assets/voices/` |
| 2 | **Edge TTS** | **Free** | Microsoft Neural voices (Indian English) | Works out of the box, no key needed |
| 3 | **Browser TTS** | Free | Basic browser voices | Automatic fallback if Edge TTS fails |

## Adding / Editing Leaders

Each leader is defined by a YAML file in `config/leaders/`. To add a new leader:

1. Create `config/leaders/your_leader.yaml` following the existing format.
2. Create a folder `assets/leaders/your_leader/`.
3. Add their **avatar image** (stylized) and **source image** (photo) to that folder.
4. *(Optional)* Add a voice sample to `assets/voices/`.

Key YAML fields:

```yaml
id: leader_id
name: Full Name
role: Title
avatar_image: assets/leaders/leader_id/avatar.png
source_image: assets/leaders/leader_id/source.png
accent_color: "#F26522"
voice_id: "en-IN-PrabhatNeural"       # Edge TTS voice
voice_sample: "assets/voices/leader.mp3"  # ElevenLabs cloning (optional)

personality:
  thinking_style: "..."
  emotional_baseline: "..."
  communication_style: "..."
  risk_appetite: "..."
  core_values: [...]
  leadership_philosophy: "..."
  decision_framework: "..."
  conflict_handling: "..."
  motivational_drivers: [...]

speech_patterns:
  - "Often says '...'"
  - "Starts sentences with '...'"

forbidden_topics:
  - Confidential data
  - Political opinions
```

Use the questionnaire in `docs/leadership_personality_questionnaire.md` to gather real personality data from leaders.

## Gamification

| XP Action | Points |
|-----------|--------|
| Ask a question | +50 XP |

Badges unlock based on questions asked and leaders chatted with. XP levels progress from **Curious Mind** to **Visionary Leader**.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit, custom CSS/HTML |
| LLM | Google Gemini 2.5 Flash |
| Avatar Generation | Gemini 2.5 Flash Image + Pillow fallback |
| TTS (free) | Edge TTS (Microsoft Neural) |
| TTS (premium) | ElevenLabs (voice cloning) |
| Config | YAML personality files |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GOOGLE_API_KEY not set` | Add it to `.streamlit/secrets.toml` or set env var. |
| Port 8501 already in use | `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess -Force` |
| Avatar generation returns original photo | Check Gemini API quota; Pillow fallback is used when Gemini is unavailable |
| No audio playing | Check browser autoplay settings; try clicking the page first |
| Edge TTS fails | Requires internet connection; falls back to browser TTS automatically |

## License

Internal — EXL AI Summit 2026.
