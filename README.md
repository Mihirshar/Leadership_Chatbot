# EXL Leadership AI — Gamified Avatar Platform

An interactive Streamlit application for the **EXL AI Summit 2026**. Visitors choose a leadership avatar, ask questions, and get personality-driven responses — complete with AI-generated avatars, text-to-speech voices, and a gamified XP system.

## Features

- **4 Leadership Avatars** — each with distinct personality, speech patterns, and values built from YAML configs
- **AI Avatar Generation** — visitors snap a photo and Gemini creates a stylized avatar on the spot
- **Voice Output (TTS)** — leaders respond with audio using cloned voices (ElevenLabs) or free neural voices (Edge TTS)
- **Gamification** — XP points, leveling, and badges earned through conversations
- **Scenario Library** — pre-built leadership scenarios visitors can tap to start a conversation

## Project Structure

```
Clawdbot/
├── app.py                        # Main Streamlit application
├── requirements.txt              # Python dependencies
├── .streamlit/config.toml        # Streamlit theme & server config
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
│       ├── nalin.yaml
│       └── anita.yaml
│
├── assets/
│   ├── avatars/                  # Leader avatar images (PNG)
│   │   └── visitors/             # Auto-generated visitor avatars
│   ├── images/                   # Source photos of leaders
│   ├── voices/                   # Voice samples for cloning (MP3, 30s-3min each)
│   └── ui/                       # Logo and UI assets
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

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key ([aistudio.google.com](https://aistudio.google.com)) |
| `ELEVENLABS_API_KEY` | No | ElevenLabs key for cloned voices ([elevenlabs.io](https://elevenlabs.io)) |

## Running the App

### Windows (PowerShell)

```powershell
$env:GOOGLE_API_KEY="your-google-api-key"
streamlit run app.py
```

### Windows (CMD)

```cmd
set GOOGLE_API_KEY=your-google-api-key
streamlit run app.py
```

### Mac / Linux

```bash
export GOOGLE_API_KEY="your-google-api-key"
streamlit run app.py
```

### With ElevenLabs (optional, for cloned voices)

```powershell
$env:GOOGLE_API_KEY="your-google-api-key"; $env:ELEVENLABS_API_KEY="your-elevenlabs-key"; streamlit run app.py
```

The app opens at **http://localhost:8501**.

## Voice System — How It Works

The app uses a 3-tier TTS priority chain. No configuration needed — it picks the best available option automatically:

| Tier | Engine | Cost | Voice Quality | Setup |
|------|--------|------|---------------|-------|
| 1 | **ElevenLabs** | ~$99/mo (Pro) | Cloned from real voice samples | Set `ELEVENLABS_API_KEY` + drop MP3 samples in `assets/voices/` |
| 2 | **Edge TTS** | **Free** | Microsoft Neural voices (Indian English) | Works out of the box, no key needed |
| 3 | **Browser TTS** | Free | Basic browser voices | Automatic fallback if Edge TTS fails |

Each leader's YAML config has:
- `voice_id` — Microsoft Neural voice name used by Edge TTS (e.g., `en-IN-PrabhatNeural`)
- `voice_sample` — path to audio clip for ElevenLabs cloning (optional)

## Adding / Editing Leaders

Each leader is defined by a YAML file in `config/leaders/`. To add a new leader:

1. Create `config/leaders/your_leader.yaml` following the existing format
2. Add their source photo to `assets/leaders/`
3. Add their avatar image to `assets/leaders/`
4. *(Optional)* Add a voice sample to `assets/voices/`

Key YAML fields:

```yaml
id: leader_id
name: Full Name
role: Title
avatar_image: assets/leaders/leader_avatar.png
source_image: assets/leaders/leader_source.jpg
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
| `GOOGLE_API_KEY not set` | Set the env var before running `streamlit run` |
| Port 8501 already in use | `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess -Force` |
| Avatar generation returns original photo | Check Gemini API quota; Pillow fallback is used when Gemini is unavailable |
| No audio playing | Check browser autoplay settings; try clicking the page first |
| Edge TTS fails | Requires internet connection; falls back to browser TTS automatically |

## License

Internal — EXL AI Summit 2026.
