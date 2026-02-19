import streamlit as st
import base64
from pathlib import Path
from core.personality_engine import load_all_leaders, get_xp_level
from core.prompt_builder import build_system_prompt
from core.llm_client import get_leader_response
from core.avatar_generator import generate_avatar, save_avatar
from core import voice_client
from components.avatar_card import render_avatar_card, render_active_avatar, render_user_active_avatar, render_tts_dialogue
from components.chat_ui import render_chat_message, render_welcome_message
from components.leaderboard import render_xp_panel, render_badges, render_insight_card
from utils.helpers import get_suggested_questions, get_scenarios, hex_to_rgba, get_image_base64

EXL_LOGO_B64 = get_image_base64("assets/ui/exl_logo.png")

st.set_page_config(
    page_title="EXL Leadership AI",
    page_icon="https://em-content.zobj.net/source/apple/391/high-voltage_26a1.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root{--exl:#F26522;--exl-r:242;--exl-g:101;--exl-b:34;--bg:#06060B;--surface:rgba(255,255,255,0.03);--border:rgba(255,255,255,0.07);}

.stApp{background:var(--bg);color:#E8E8F0;font-family:'Inter',-apple-system,sans-serif;}
.stApp>header{background:transparent!important;}
.block-container{padding-top:1rem!important;max-width:1500px;}
#MainMenu,footer,.stDeployButton{display:none!important;}

/* ── Top brand accent bar ── */
.stApp::before{
    content:'';position:fixed;top:0;left:0;right:0;height:3px;z-index:9999;
    background:linear-gradient(90deg,transparent 5%,var(--exl) 30%,#F4943E 70%,transparent 95%);
    opacity:0.85;
}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.25);border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.4);}

/* ── Buttons: secondary (default) ── */
.stButton>button{
    background:linear-gradient(135deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))!important;
    border:1px solid var(--border)!important;
    color:#E8E8F0!important;border-radius:12px!important;
    padding:10px 20px!important;font-family:'Inter',sans-serif!important;
    font-weight:500!important;font-size:0.82rem!important;
    transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important;
}
.stButton>button:hover{
    border-color:rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.5)!important;
    background:linear-gradient(135deg,rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.12),rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.04))!important;
    box-shadow:0 0 20px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.15)!important;
}

/* ── Buttons: primary (EXL orange filled) ── */
.stButton>button[kind="primary"],
.stButton>button[data-testid="stBaseButton-primary"]{
    background:linear-gradient(135deg,#F26522,#E85D26)!important;
    border:1px solid rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.6)!important;
    color:#fff!important;font-weight:600!important;
    box-shadow:0 2px 12px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.25)!important;
}
.stButton>button[kind="primary"]:hover,
.stButton>button[data-testid="stBaseButton-primary"]:hover{
    background:linear-gradient(135deg,#E85D26,#D4551E)!important;
    box-shadow:0 4px 24px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.4)!important;
}

/* ── Text inputs / textareas ── */
input[type="text"],textarea,[data-testid="stTextInput"] input{
    background:rgba(255,255,255,0.04)!important;
    border:1px solid var(--border)!important;
    color:#E8E8F0!important;border-radius:10px!important;
    font-family:'Inter',sans-serif!important;
}
input[type="text"]:focus,textarea:focus,[data-testid="stTextInput"] input:focus{
    border-color:rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.5)!important;
    box-shadow:0 0 0 2px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.15)!important;
}
[data-testid="stTextInput"] label{color:rgba(255,255,255,0.5)!important;font-size:0.78rem!important;font-weight:500!important;}

/* ── Chat input ── */
[data-testid="stChatInput"]{background:transparent!important;}
[data-testid="stChatInput"] textarea{color:#E8E8F0!important;font-family:'Inter',sans-serif!important;}

/* ── Chat messages ── */
[data-testid="stChatMessage"]{
    background:var(--surface)!important;
    border:1px solid var(--border)!important;
    border-radius:14px!important;padding:14px 18px!important;
    margin-bottom:8px!important;
}
[data-testid="stChatMessage"] p{color:#E8E8F0!important;line-height:1.6!important;}
[data-testid="stChatMessage"] img{border-radius:50%!important;border:2px solid rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.4)!important;}

/* ── Progress bar — EXL orange gradient ── */
.stProgress>div>div{
    background:linear-gradient(90deg,#E85D26,var(--exl),#F4943E)!important;
    border-radius:100px!important;
}
.stProgress>div{background:rgba(255,255,255,0.06)!important;border-radius:100px!important;height:8px!important;}

/* ── Metric override ── */
[data-testid="stMetric"]{
    background:var(--surface)!important;
    border:1px solid var(--border)!important;
    border-radius:12px!important;padding:12px!important;
    text-align:center;
}
[data-testid="stMetricValue"]{color:var(--exl)!important;font-size:1.4rem!important;font-weight:700!important;}
[data-testid="stMetricLabel"]{color:rgba(255,255,255,0.4)!important;font-size:0.65rem!important;text-transform:uppercase!important;letter-spacing:0.04em!important;}
[data-testid="stMetricDelta"]{display:none!important;}

/* ── Info boxes ── */
[data-testid="stAlert"]{
    background:rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.06)!important;
    border:1px solid rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.15)!important;
    border-radius:12px!important;color:#E8E8F0!important;
}

/* ── Camera & file uploader ── */
[data-testid="stCameraInput"]>div,[data-testid="stFileUploader"]>div>div{
    background:rgba(255,255,255,0.03)!important;
    border:1px dashed rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.25)!important;
    border-radius:12px!important;
}
[data-testid="stCameraInput"] button{
    border-color:rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.4)!important;
}

/* ── Scrollable containers ── */
[data-testid="stVerticalBlockBorderWrapper"]{
    border-color:var(--border)!important;border-radius:14px!important;
}

/* ── Typography ── */
h1,h2,h3{font-family:'Syne',sans-serif!important;letter-spacing:-0.02em;}
hr{border-color:var(--border)!important;}

/* ── Column spacing ── */
[data-testid="column"]{padding:0 8px;overflow:hidden;}

/* ── Animations ── */
@keyframes avatarFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@keyframes idlePulse{
    0%,100%{box-shadow:0 0 25px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.3),0 0 50px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.1);}
    50%{box-shadow:0 0 35px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.5),0 0 70px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.2);}
}
@keyframes speakingPulse{
    0%,100%{box-shadow:0 0 30px rgba(74,222,128,0.4),0 0 60px rgba(74,222,128,0.15);border-color:rgba(74,222,128,0.8);}
    50%{box-shadow:0 0 45px rgba(74,222,128,0.6),0 0 80px rgba(74,222,128,0.3);border-color:rgba(74,222,128,1);}
}
@keyframes soundWave{0%,100%{transform:scaleY(0.25)}25%{transform:scaleY(0.85)}50%{transform:scaleY(0.5)}75%{transform:scaleY(1)}}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes gridScroll{0%{transform:translate(0,0)}100%{transform:translate(30px,30px)}}
@keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes badgePop{0%{opacity:0;transform:scale(0.85)}60%{transform:scale(1.05)}100%{opacity:1;transform:scale(1)}}
@keyframes glowDot{0%,100%{opacity:0.4}50%{opacity:1}}
@keyframes accentSlide{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}
</style>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "selected_leader": None,
        "conversation": [],
        "xp": 0,
        "questions_asked": 0,
        "leaders_chatted_set": set(),
        "show_consent": True,
        "show_photo_setup": True,
        "pending_question": None,
        "tts_pending": False,
        "last_user_text": None,
        "last_leader_text": None,
        "last_leader_audio_b64": None,
        "user_name": "",
        "user_avatar_path": None,
        "user_original_photo": None,
        "user_generated_avatar": None,
        "who_speaking": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


@st.cache_data
def load_leaders():
    return load_all_leaders()

leaders = load_leaders()


# ---------------------------------------------------------------------------
# Consent screen
# ---------------------------------------------------------------------------
def render_consent():
    # Ambient grid
    st.markdown(
        '<div style="position:fixed;top:0;left:0;width:100%;height:100%;'
        'background-image:linear-gradient(rgba(242,101,34,0.015) 1px,transparent 1px),'
        'linear-gradient(90deg,rgba(242,101,34,0.015) 1px,transparent 1px);'
        'background-size:40px 40px;animation:gridScroll 12s linear infinite;'
        'pointer-events:none;z-index:0;"></div>',
        unsafe_allow_html=True,
    )

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown("&nbsp;", unsafe_allow_html=True)
    _c1, center, _c2 = st.columns([1, 1.8, 1])
    with center:
        st.markdown(
            f'<div style="text-align:center;animation:fadeIn 0.7s ease-out;">'
            f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:60px;margin-bottom:24px;filter:drop-shadow(0 0 40px rgba(242,101,34,0.35));" />'
            f'<div style="width:50px;height:2px;background:linear-gradient(90deg,transparent,#F26522,transparent);margin:0 auto 20px;"></div>'
            f'<h1 style="font-family:Syne,sans-serif;font-size:2.4rem;font-weight:800;'
            f'color:#F0F0F8;margin-bottom:6px;line-height:1.1;">Leadership AI</h1>'
            f'<p style="font-size:0.78rem;color:rgba(255,255,255,0.3);letter-spacing:0.14em;'
            f'text-transform:uppercase;font-weight:500;margin-bottom:32px;">'
            f'AI Summit 2026 &middot; Gamified Leadership Conversations</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div style="background:rgba(242,101,34,0.05);border:1px solid rgba(242,101,34,0.12);'
            'border-radius:14px;padding:18px 22px;margin-bottom:24px;">'
            '<p style="margin:0;font-size:0.82rem;color:rgba(255,255,255,0.55);line-height:1.6;">'
            '<strong style="color:rgba(255,255,255,0.7);">Disclaimer:</strong> '
            'This experience features AI-simulated avatars inspired by leadership personas. '
            'Responses are generated by AI and <strong>do not represent the actual views, '
            'opinions, or statements</strong> of any real individual. '
            'This is a demonstration for the EXL AI Summit.</p></div>',
            unsafe_allow_html=True,
        )

        if st.button("I Understand — Enter the Experience", use_container_width=True, type="primary"):
            st.session_state.show_consent = False
            st.rerun()


# ---------------------------------------------------------------------------
# Photo setup screen
# ---------------------------------------------------------------------------
def _save_user_photo(photo_bytes: bytes, name: str) -> str:
    safe_name = "".join(c if c.isalnum() else "_" for c in name.strip().lower()) or "visitor"
    out_dir = Path("assets/avatars/visitors")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{safe_name}.png"
    out_path.write_bytes(photo_bytes)
    return str(out_path)


def render_photo_setup():
    # Ambient grid
    st.markdown(
        '<div style="position:fixed;top:0;left:0;width:100%;height:100%;'
        'background-image:linear-gradient(rgba(242,101,34,0.012) 1px,transparent 1px),'
        'linear-gradient(90deg,rgba(242,101,34,0.012) 1px,transparent 1px);'
        'background-size:40px 40px;animation:gridScroll 12s linear infinite;'
        'pointer-events:none;z-index:0;"></div>',
        unsafe_allow_html=True,
    )

    st.markdown("&nbsp;", unsafe_allow_html=True)
    _c1, center, _c2 = st.columns([1, 2, 1])
    with center:
        st.markdown(
            f'<div style="text-align:center;animation:fadeIn 0.6s ease-out;">'
            f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:36px;margin-bottom:14px;filter:drop-shadow(0 0 25px rgba(242,101,34,0.25));" />'
            f'<div style="width:40px;height:2px;background:linear-gradient(90deg,transparent,#F26522,transparent);margin:0 auto 14px;"></div>'
            f'<h1 style="font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;color:#F0F0F8;margin-bottom:4px;">Create Your Avatar</h1>'
            f'<p style="font-size:0.85rem;color:rgba(255,255,255,0.4);margin-bottom:24px;">'
            f'Snap a photo or upload one — AI will generate your personalised avatar!</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        user_name = st.text_input(
            "Your Name",
            placeholder="e.g. Rahul Sharma",
            max_chars=40,
        )

        st.markdown(
            '<p style="font-size:0.72rem;color:rgba(255,255,255,0.35);text-transform:uppercase;'
            'letter-spacing:0.08em;font-weight:600;margin:20px 0 8px;">Option 1 — Use your webcam</p>',
            unsafe_allow_html=True,
        )
        camera_photo = st.camera_input("Take a photo", label_visibility="collapsed")

        st.markdown(
            '<p style="font-size:0.72rem;color:rgba(255,255,255,0.35);text-transform:uppercase;'
            'letter-spacing:0.08em;font-weight:600;margin:20px 0 8px;">Option 2 — Upload a photo</p>',
            unsafe_allow_html=True,
        )
        uploaded_photo = st.file_uploader(
            "Upload photo",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )

        photo_data = camera_photo or uploaded_photo

        # ---------- Preview: original + generated avatar side by side ----------
        if photo_data:
            photo_bytes = photo_data.getvalue()
            b64_original = base64.b64encode(photo_bytes).decode()
            st.session_state.user_original_photo = photo_bytes

            has_avatar = st.session_state.user_generated_avatar is not None

            if has_avatar:
                b64_gen = base64.b64encode(st.session_state.user_generated_avatar).decode()
                st.markdown(
                    f'<div style="display:flex;align-items:center;justify-content:center;gap:24px;margin:20px 0;">'
                    f'<div style="text-align:center;">'
                    f'<p style="font-size:0.65rem;color:rgba(255,255,255,0.35);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">Your Photo</p>'
                    f'<img src="data:image/png;base64,{b64_original}" style="width:100px;height:100px;object-fit:cover;border-radius:50%;border:2px solid rgba(255,255,255,0.15);opacity:0.7;" /></div>'
                    f'<div style="display:flex;flex-direction:column;align-items:center;gap:2px;">'
                    f'<span style="font-size:1.2rem;">&#x27A1;</span>'
                    f'<span style="font-size:0.55rem;color:rgba(255,255,255,0.3);">AI</span></div>'
                    f'<div style="text-align:center;">'
                    f'<p style="font-size:0.65rem;color:#F26522;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;margin-bottom:8px;">Your Avatar</p>'
                    f'<img src="data:image/png;base64,{b64_gen}" style="width:120px;height:120px;object-fit:cover;border-radius:50%;border:3px solid #F26522;box-shadow:0 0 30px rgba(242,101,34,0.35);" /></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="text-align:center;margin:16px 0;">'
                    f'<p style="font-size:0.72rem;color:rgba(255,255,255,0.4);margin-bottom:8px;">Your Photo</p>'
                    f'<img src="data:image/png;base64,{b64_original}" style="width:120px;height:120px;'
                    f'object-fit:cover;border-radius:50%;border:3px solid rgba(255,255,255,0.15);'
                    f'box-shadow:0 0 20px rgba(255,255,255,0.05);"/></div>',
                    unsafe_allow_html=True,
                )

            # Generate avatar button
            if not has_avatar:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("Generate AI Avatar", use_container_width=True, type="primary", disabled=not user_name.strip()):
                    with st.spinner("Gemini is creating your avatar — hold tight..."):
                        avatar_bytes, method = generate_avatar(photo_bytes)
                    st.session_state.user_generated_avatar = avatar_bytes
                    if method == "gemini":
                        st.toast("Avatar generated by Gemini AI!", icon="✨")
                    else:
                        st.toast("Avatar created with artistic filters (Gemini unavailable)", icon="🎨")
                    st.rerun()
            else:
                if st.button("Regenerate Avatar", use_container_width=True):
                    st.session_state.user_generated_avatar = None
                    st.rerun()

        st.markdown("&nbsp;", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            can_continue_avatar = bool(
                user_name.strip()
                and photo_data
                and st.session_state.user_generated_avatar
            )
            if st.button(
                "Use AI Avatar",
                use_container_width=True,
                type="primary",
                disabled=not can_continue_avatar,
            ):
                path = save_avatar(st.session_state.user_generated_avatar, user_name)
                st.session_state.user_name = user_name.strip()
                st.session_state.user_avatar_path = path
                st.session_state.show_photo_setup = False
                st.rerun()
        with col_b:
            can_continue_photo = bool(user_name.strip() and photo_data)
            if st.button(
                "Use Original Photo",
                use_container_width=True,
                disabled=not can_continue_photo,
            ):
                path = _save_user_photo(photo_data.getvalue(), user_name)
                st.session_state.user_name = user_name.strip()
                st.session_state.user_avatar_path = path
                st.session_state.show_photo_setup = False
                st.rerun()
        with col_c:
            if st.button("Skip — Guest Mode", use_container_width=True):
                st.session_state.user_name = "You"
                st.session_state.user_avatar_path = None
                st.session_state.show_photo_setup = False
                st.rerun()


# ---------------------------------------------------------------------------
# Leader selection screen
# ---------------------------------------------------------------------------
def render_leader_selection():
    # Ambient grid
    st.markdown(
        '<div style="position:fixed;top:0;left:0;width:100%;height:100%;'
        'background-image:linear-gradient(rgba(242,101,34,0.012) 1px,transparent 1px),'
        'linear-gradient(90deg,rgba(242,101,34,0.012) 1px,transparent 1px);'
        'background-size:40px 40px;animation:gridScroll 12s linear infinite;'
        'pointer-events:none;z-index:0;"></div>',
        unsafe_allow_html=True,
    )

    user_name = st.session_state.user_name
    greeting = f", {user_name}" if user_name and user_name != "You" else ""

    st.markdown(
        f'<div style="text-align:center;padding:12px 0 4px;animation:fadeIn 0.6s ease-out;">'
        f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:42px;margin-bottom:12px;filter:drop-shadow(0 0 30px rgba(242,101,34,0.3));" />'
        f'<div style="width:40px;height:2px;background:linear-gradient(90deg,transparent,#F26522,transparent);margin:0 auto 12px;"></div>'
        f'<h1 style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;'
        f'color:#F0F0F8;margin-bottom:4px;">Leadership AI</h1>'
        f'<p style="font-size:0.82rem;color:rgba(255,255,255,0.35);letter-spacing:0.1em;'
        f'text-transform:uppercase;font-weight:500;">Choose Your Leader{greeting} &middot; Ask Anything &middot; Earn XP</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("&nbsp;", unsafe_allow_html=True)

    cols = st.columns(len(leaders), gap="medium")
    for i, (lid, leader) in enumerate(leaders.items()):
        with cols[i]:
            if render_avatar_card(leader):
                st.session_state.selected_leader = lid
                st.session_state.conversation = []
                st.session_state.tts_pending = False
                st.session_state.last_user_text = None
                st.session_state.last_leader_text = None
                st.session_state.last_leader_audio_b64 = None
                st.session_state.leaders_chatted_set.add(lid)
                st.rerun()

    if st.session_state.xp > 0:
        level, title, _ = get_xp_level(st.session_state.xp)
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.markdown(
            f'<div style="text-align:center;padding:14px;background:rgba(255,255,255,0.02);'
            f'border:1px solid rgba(255,255,255,0.06);border-radius:14px;">'
            f'<span style="font-size:0.78rem;color:rgba(255,255,255,0.4);">Your progress &mdash; </span>'
            f'<span style="font-size:0.82rem;color:#F26522;font-weight:600;">Level {level} {title}</span>'
            f'<span style="font-size:0.78rem;color:rgba(255,255,255,0.4);"> &mdash; {st.session_state.xp} XP &middot; {st.session_state.questions_asked} questions</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Chat screen
# ---------------------------------------------------------------------------
def render_chat_screen():
    leader = leaders[st.session_state.selected_leader]
    accent = leader.get("accent_color", "#F26522")
    system_prompt = build_system_prompt(leader)
    user_name = st.session_state.user_name or "You"

    who = st.session_state.who_speaking
    leader_speaking = who == "leader"
    user_speaking = who == "user"

    # Consume TTS flag for this render (plays once via a single component)
    tts_dialogue = None
    if st.session_state.tts_pending:
        st.session_state.tts_pending = False
        tts_dialogue = (
            st.session_state.last_user_text,
            st.session_state.last_leader_text,
        )

    # ── Top bar: logo + header + exchange count ──
    exchange_count = len([m for m in st.session_state.conversation if m["role"] == "user"])
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;'
        f'padding:8px 18px;background:rgba(255,255,255,0.02);'
        f'border:1px solid rgba(255,255,255,0.06);border-radius:12px;margin-bottom:10px;">'
        f'<div style="display:flex;align-items:center;gap:10px;">'
        f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:18px;opacity:0.7;" />'
        f'<div style="width:1px;height:18px;background:rgba(255,255,255,0.08);"></div>'
        f'<span style="font-family:Syne,sans-serif;font-size:0.78rem;font-weight:600;color:#F0F0F8;">'
        f'Leadership AI</span>'
        f'<div style="width:6px;height:6px;border-radius:50%;background:#4ADE80;'
        f'box-shadow:0 0 6px rgba(74,222,128,0.5);animation:glowDot 2s ease-in-out infinite;"></div>'
        f'</div>'
        f'<span style="font-size:0.65rem;color:rgba(255,255,255,0.25);font-family:JetBrains Mono,monospace;">'
        f'{exchange_count} exchanges</span></div>',
        unsafe_allow_html=True,
    )

    left_col, chat_col, right_col = st.columns([1.0, 3.0, 1.0], gap="large")

    # ══════════════════════════════════════════════════════════════════════
    # LEFT PANEL — Leader avatar + XP + badges
    # ══════════════════════════════════════════════════════════════════════
    with left_col:
        render_active_avatar(
            leader,
            is_speaking=leader_speaking or bool(tts_dialogue),
        )

        st.markdown(
            f'<div style="width:100%;height:1px;'
            f'background:linear-gradient(90deg,transparent,{hex_to_rgba(accent, 0.3)},transparent);'
            f'margin:4px 0 12px;"></div>',
            unsafe_allow_html=True,
        )

        render_xp_panel(
            st.session_state.xp,
            st.session_state.questions_asked,
            len(st.session_state.leaders_chatted_set),
            len(leaders),
        )

        st.markdown(
            '<p style="font-family:Syne,sans-serif;font-size:0.7rem;font-weight:700;'
            'color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.08em;'
            'margin:12px 0 6px;">Badges</p>',
            unsafe_allow_html=True,
        )
        render_badges(
            st.session_state.questions_asked,
            len(st.session_state.leaders_chatted_set),
            len(leaders),
        )

        if st.button("← Switch Leader", use_container_width=True):
            st.session_state.selected_leader = None
            st.session_state.tts_pending = False
            st.session_state.last_user_text = None
            st.session_state.last_leader_text = None
            st.session_state.last_leader_audio_b64 = None
            st.session_state.who_speaking = None
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # RIGHT PANEL — User avatar + scenarios
    # ══════════════════════════════════════════════════════════════════════
    with right_col:
        render_user_active_avatar(
            avatar_path=st.session_state.user_avatar_path,
            user_name=user_name,
            is_speaking=user_speaking or bool(tts_dialogue),
        )

        st.markdown(
            '<div style="width:100%;height:1px;'
            'background:linear-gradient(90deg,transparent,rgba(242,101,34,0.25),transparent);'
            'margin:4px 0 12px;"></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-family:Syne,sans-serif;font-size:0.7rem;font-weight:700;'
            'color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:0.08em;'
            'margin:0 0 8px;">Scenarios</p>',
            unsafe_allow_html=True,
        )

        scenarios_container = st.container(height=340)
        with scenarios_container:
            for cat in get_scenarios():
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:5px;margin:8px 0 4px;">'
                    f'<span style="font-size:0.8rem;">{cat["icon"]}</span>'
                    f'<span style="font-family:Syne,sans-serif;font-size:0.62rem;font-weight:700;'
                    f'color:rgba(255,255,255,0.45);text-transform:uppercase;letter-spacing:0.05em;">'
                    f'{cat["category"]}</span></div>',
                    unsafe_allow_html=True,
                )
                for item in cat["items"]:
                    if st.button(
                        item["title"],
                        key=f"sc_{item['title'][:20]}",
                        use_container_width=True,
                    ):
                        st.session_state.pending_question = item["prompt"]
                        st.rerun()

        # EXL footer badge
        st.markdown(
            f'<div style="text-align:center;margin:10px 0 4px;padding:10px 8px;'
            f'background:rgba(242,101,34,0.03);border:1px solid rgba(242,101,34,0.08);border-radius:10px;">'
            f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:16px;opacity:0.5;" />'
            f'<p style="font-size:0.55rem;color:rgba(255,255,255,0.2);margin:4px 0 0;letter-spacing:0.06em;text-transform:uppercase;">'
            f'AI Summit 2026</p></div>',
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════
    # CENTER PANEL — Chat
    # ══════════════════════════════════════════════════════════════════════
    with chat_col:
        chat_container = st.container(height=500)
        with chat_container:
            if not st.session_state.conversation:
                render_welcome_message(leader, user_name=st.session_state.user_name)
            else:
                for msg in st.session_state.conversation:
                    render_chat_message(
                        msg["role"],
                        msg["content"],
                        leader=leader if msg["role"] == "assistant" else None,
                        user_avatar_path=st.session_state.user_avatar_path,
                    )

                assistant_msgs = [m for m in st.session_state.conversation if m["role"] == "assistant"]
                if len(assistant_msgs) > 0 and len(assistant_msgs) % 3 == 0:
                    first_sentence = assistant_msgs[-1]["content"].split(".")[0] + "."
                    render_insight_card(first_sentence, leader["name"], accent)

        if tts_dialogue:
            render_tts_dialogue(
                user_text=tts_dialogue[0],
                leader_text=tts_dialogue[1],
                leader_name=leader["name"],
                leader_audio_b64=st.session_state.last_leader_audio_b64,
            )

        user_input = st.chat_input(f"Ask {leader['name']} anything...")

        if st.session_state.pending_question:
            user_input = st.session_state.pending_question
            st.session_state.pending_question = None

        if user_input:
            st.session_state.who_speaking = "user"
            st.session_state.conversation.append({"role": "user", "content": user_input})

            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.conversation[:-1]
            ]

            try:
                full_response = get_leader_response(system_prompt, history, user_input)
            except Exception as e:
                full_response = f"*Connection issue — please ensure GOOGLE_API_KEY is set.* (`{e}`)"

            st.session_state.conversation.append({"role": "assistant", "content": full_response})
            st.session_state.xp += 50
            st.session_state.questions_asked += 1
            st.session_state.who_speaking = "leader"

            if not full_response.startswith("*Connection issue"):
                st.session_state.tts_pending = True
                st.session_state.last_user_text = user_input
                st.session_state.last_leader_text = full_response

                st.session_state.last_leader_audio_b64 = None
                audio_bytes = voice_client.synthesize_for_leader(leader, full_response)
                if audio_bytes:
                    st.session_state.last_leader_audio_b64 = base64.b64encode(audio_bytes).decode()

            st.rerun()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
def main():
    if st.session_state.show_consent:
        render_consent()
    elif st.session_state.show_photo_setup:
        render_photo_setup()
    elif st.session_state.selected_leader is None:
        render_leader_selection()
    else:
        render_chat_screen()

if __name__ == "__main__":
    main()
