import streamlit as st
import base64
import re
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
    page_icon="assets/ui/favicon.png",
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

/* ── Buttons: primary (EXL orange filled + glow) ── */
.stButton>button[kind="primary"],
.stButton>button[data-testid="stBaseButton-primary"]{
    background:linear-gradient(135deg,#F26522,#E85D26,#F4943E)!important;
    background-size:200% 100%!important;
    border:1px solid rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.6)!important;
    color:#fff!important;font-weight:600!important;font-size:0.88rem!important;
    padding:14px 28px!important;border-radius:14px!important;
    box-shadow:0 4px 20px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.3),0 0 40px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.1)!important;
    animation:shimmer 3s linear infinite!important;
    transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important;
}
.stButton>button[kind="primary"]:hover,
.stButton>button[data-testid="stBaseButton-primary"]:hover{
    background:linear-gradient(135deg,#E85D26,#D4551E,#F26522)!important;
    background-size:200% 100%!important;
    box-shadow:0 6px 30px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.5),0 0 60px rgba(var(--exl-r),var(--exl-g),var(--exl-b),0.2)!important;
    transform:translateY(-2px)!important;
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

/* ── Use Cases Panel ── */
.use-cases-section {
    position: relative;
    padding: 16px 12px;
    background: linear-gradient(165deg, rgba(242,101,34,0.04), rgba(139,92,246,0.02), transparent);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    margin-top: 4px;
}
.use-cases-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(242,101,34,0.4), rgba(139,92,246,0.3), transparent);
    border-radius: 16px 16px 0 0;
}
.use-cases-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    padding-bottom: 2px;
    min-height: 28px;
}
.use-cases-title span.icon {
    width: 18px;
    height: 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.95rem;
    line-height: 1;
}
.use-cases-title span.text {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    line-height: 1;
    display: inline-flex;
    align-items: center;
}
.use-cases-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
/* Hide default Streamlit container border in use cases */
.use-cases-section [data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    background: transparent !important;
}

/* ── Expander (Use Case Categories) ── */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02)) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: rgba(255,255,255,0.85) !important;
    transition: all 0.25s ease !important;
    line-height: 1.35 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
}
.streamlit-expanderHeader p,
.streamlit-expanderHeader span {
    margin: 0 !important;
    white-space: normal !important;
    word-break: keep-all !important;
    overflow-wrap: normal !important;
    line-height: 1.35 !important;
}
.streamlit-expanderHeader:hover {
    background: linear-gradient(135deg, rgba(242,101,34,0.12), rgba(242,101,34,0.05)) !important;
    border-color: rgba(242,101,34,0.35) !important;
    color: #F26522 !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(242,101,34,0.15) !important;
}
.streamlit-expanderHeader[aria-expanded="true"] {
    background: linear-gradient(135deg, rgba(242,101,34,0.14), rgba(242,101,34,0.06)) !important;
    border-color: rgba(242,101,34,0.4) !important;
    color: #F26522 !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    box-shadow: 0 8px 24px rgba(242,101,34,0.18) !important;
}
.streamlit-expanderContent {
    background: rgba(6,6,11,0.6) !important;
    border: 1px solid rgba(242,101,34,0.15) !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    padding: 12px 10px !important;
    backdrop-filter: blur(8px);
}
.streamlit-expanderContent .stButton > button {
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02)) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 0.76rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    color: rgba(255,255,255,0.75) !important;
    margin-bottom: 6px !important;
    line-height: 1.4 !important;
    white-space: normal !important;
    transition: all 0.2s ease !important;
    word-break: keep-all !important;
}
.streamlit-expanderContent .stButton > button:hover {
    background: linear-gradient(135deg, rgba(242,101,34,0.12), rgba(242,101,34,0.06)) !important;
    border-color: rgba(242,101,34,0.4) !important;
    color: #F26522 !important;
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(242,101,34,0.12) !important;
}

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
@keyframes fadeInUp{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:translateY(0)}}
@keyframes gridScroll{0%{transform:translate(0,0)}100%{transform:translate(30px,30px)}}
@keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes badgePop{0%{opacity:0;transform:scale(0.85)}60%{transform:scale(1.05)}100%{opacity:1;transform:scale(1)}}
@keyframes glowDot{0%,100%{opacity:0.4}50%{opacity:1}}
@keyframes accentSlide{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}

/* ── Floating orbs ── */
@keyframes orbFloat1{0%{transform:translate(0,0) scale(1)}33%{transform:translate(60px,-80px) scale(1.1)}66%{transform:translate(-40px,50px) scale(0.9)}100%{transform:translate(0,0) scale(1)}}
@keyframes orbFloat2{0%{transform:translate(0,0) scale(1)}33%{transform:translate(-70px,60px) scale(0.85)}66%{transform:translate(50px,-40px) scale(1.15)}100%{transform:translate(0,0) scale(1)}}
@keyframes orbFloat3{0%{transform:translate(0,0) scale(1)}50%{transform:translate(40px,70px) scale(1.2)}100%{transform:translate(0,0) scale(1)}}
@keyframes orbFloat4{0%{transform:translate(0,0)}25%{transform:translate(-50px,-60px)}50%{transform:translate(30px,-30px)}75%{transform:translate(-20px,50px)}100%{transform:translate(0,0)}}
@keyframes titleGlow{0%,100%{text-shadow:0 0 30px rgba(242,101,34,0.3),0 0 60px rgba(242,101,34,0.1)}50%{text-shadow:0 0 50px rgba(242,101,34,0.5),0 0 100px rgba(242,101,34,0.2)}}
@keyframes borderRotate{0%{--angle:0deg}100%{--angle:360deg}}
@keyframes particleDrift{0%{transform:translateY(0) translateX(0);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateY(-100vh) translateX(30px);opacity:0}}
@keyframes ringPulse{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:0.15}50%{transform:translate(-50%,-50%) scale(1.15);opacity:0.08}}
@keyframes ringRotate{0%{transform:translate(-50%,-50%) rotate(0deg)}100%{transform:translate(-50%,-50%) rotate(360deg)}}
@keyframes ringRotateR{0%{transform:translate(-50%,-50%) rotate(360deg)}100%{transform:translate(-50%,-50%) rotate(0deg)}}
@keyframes streak{0%{transform:translateX(-100%) translateY(100%);opacity:0}30%{opacity:0.5}70%{opacity:0.5}100%{transform:translateX(200%) translateY(-200%);opacity:0}}
@keyframes constellationPulse{0%,100%{opacity:0.3;transform:scale(1)}50%{opacity:0.8;transform:scale(1.5)}}
@keyframes cardBorderFlow{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes floatIcon{0%,100%{transform:translateY(0) rotate(0deg);opacity:0.12}50%{transform:translateY(-15px) rotate(10deg);opacity:0.2}}

/* ── Loading pulse (vibe match) ── */
@keyframes vibePulse {
    0%, 100% { opacity: 0.3; transform: scale(0.95); box-shadow: 0 0 0 rgba(242,101,34,0); }
    50% { opacity: 1; transform: scale(1.05); box-shadow: 0 0 20px rgba(242,101,34,0.3); }
}
.vibe-loader {
    display: inline-block;
    width: 8px; height: 8px;
    background: #F26522;
    border-radius: 50%;
    margin: 0 3px;
    animation: vibePulse 1.2s infinite ease-in-out both;
}
.vibe-loader:nth-child(1) { animation-delay: -0.32s; background: #F26522; }
.vibe-loader:nth-child(2) { animation-delay: -0.16s; background: #8B5CF6; }
.vibe-loader:nth-child(3) { animation-delay: 0s; background: #2DD4BF; }

/* ── Dynamic Lip Sync (JS Driven) ── */
.avatar-wrapper.speaking .avatar-ring {
    animation: speakingPulse 0.4s ease-in-out infinite alternate !important;
    border-color: #4ADE80 !important;
    box-shadow: 0 0 35px rgba(74,222,128,0.5), 0 0 70px rgba(74,222,128,0.2) !important;
    transform: scale(1.02);
}
.avatar-wrapper.speaking img {
    animation: lipSync 0.15s ease-in-out infinite alternate;
}
@keyframes lipSync { 0% { transform: scale(1); } 100% { transform: scale(1, 0.98); } }

.avatar-wrapper.speaking .wave-bar {
    animation: soundWave 0.5s ease-in-out infinite !important;
    opacity: 1 !important;
    background: #4ADE80 !important;
}
.avatar-wrapper.speaking .status-text { color: #4ADE80 !important; }
.avatar-wrapper.speaking .status-text span { display: none; }
.avatar-wrapper.speaking .status-text::after { content: "SPEAKING"; }

/* Initial state overrides to support JS toggling */
.avatar-wrapper .avatar-ring { transition: all 0.3s ease; }
.avatar-wrapper .wave-bar { transition: all 0.3s ease; }
.avatar-wrapper .status-text { transition: color 0.3s ease; }

/* ══════════════════════════════════════════════════════════════════════════
   MOBILE RESPONSIVE STYLES
   ══════════════════════════════════════════════════════════════════════════ */

/* ── Mobile Chat Header with Prominent Leader Avatar ── */
.mobile-chat-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    background: linear-gradient(135deg, rgba(242,101,34,0.08), rgba(139,92,246,0.05));
    border: 1px solid rgba(242,101,34,0.15);
    border-radius: 16px;
    margin-bottom: 10px;
}
.mobile-chat-header .leader-avatar {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    border: 3px solid var(--exl);
    box-shadow: 0 0 20px rgba(242,101,34,0.3);
    object-fit: cover;
    flex-shrink: 0;
}
.mobile-chat-header .leader-info {
    flex: 1;
    min-width: 0;
}
.mobile-chat-header .leader-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #F0F0F8;
    margin: 0 0 2px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mobile-chat-header .leader-title {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.5);
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mobile-chat-header .switch-btn {
    padding: 10px 16px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    color: rgba(255,255,255,0.7);
    font-size: 0.72rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.mobile-chat-header .switch-btn:hover {
    background: rgba(242,101,34,0.15);
    border-color: rgba(242,101,34,0.4);
    color: var(--exl);
}

/* ── Use Cases FAB (Floating Action Button) ── */
.use-cases-fab {
    position: fixed;
    bottom: 80px;
    right: 16px;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #F26522, #E85D26);
    border: none;
    color: white;
    font-size: 1.4rem;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(242,101,34,0.4), 0 0 30px rgba(242,101,34,0.2);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}
.use-cases-fab:hover {
    transform: scale(1.08);
    box-shadow: 0 6px 28px rgba(242,101,34,0.5), 0 0 40px rgba(242,101,34,0.3);
}
.use-cases-fab.active {
    transform: rotate(45deg);
    background: rgba(255,255,255,0.1);
    box-shadow: none;
}

/* ── Bottom Sheet ── */
.bottom-sheet-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    z-index: 1001;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
}
.bottom-sheet-overlay.active {
    opacity: 1;
    pointer-events: auto;
}

.bottom-sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    max-height: 70vh;
    background: #0a0a10;
    border-top-left-radius: 20px;
    border-top-right-radius: 20px;
    border: 1px solid rgba(255,255,255,0.1);
    border-bottom: none;
    z-index: 1002;
    transform: translateY(100%);
    transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.bottom-sheet.active {
    transform: translateY(0);
}

.bottom-sheet-handle {
    width: 40px;
    height: 4px;
    background: rgba(255,255,255,0.2);
    border-radius: 2px;
    margin: 12px auto 8px;
    flex-shrink: 0;
}

.bottom-sheet-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 20px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    flex-shrink: 0;
}
.bottom-sheet-header h3 {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #F0F0F8;
    margin: 0;
}
.bottom-sheet-close {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.5);
    font-size: 1.2rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}
.bottom-sheet-close:hover {
    background: rgba(242,101,34,0.1);
    border-color: rgba(242,101,34,0.3);
    color: var(--exl);
}

.bottom-sheet-content {
    flex: 1;
    overflow-y: auto;
    padding: 12px 16px 24px;
    -webkit-overflow-scrolling: touch;
}

.bottom-sheet-category {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    margin-bottom: 8px;
    overflow: hidden;
}
.bottom-sheet-category-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.2s ease;
}
.bottom-sheet-category-header:hover {
    background: rgba(242,101,34,0.05);
}
.bottom-sheet-category-header.expanded {
    background: rgba(242,101,34,0.08);
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.bottom-sheet-category-header .icon {
    font-size: 1.1rem;
}
.bottom-sheet-category-header .name {
    flex: 1;
    font-size: 0.85rem;
    font-weight: 600;
    color: rgba(255,255,255,0.8);
}
.bottom-sheet-category-header .arrow {
    color: rgba(255,255,255,0.3);
    transition: transform 0.2s ease;
}
.bottom-sheet-category-header.expanded .arrow {
    transform: rotate(90deg);
    color: var(--exl);
}

.bottom-sheet-category-items {
    display: none;
    padding: 8px;
}
.bottom-sheet-category-items.expanded {
    display: block;
}
.bottom-sheet-item {
    display: block;
    width: 100%;
    padding: 12px 14px;
    background: transparent;
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    margin-bottom: 4px;
    text-align: left;
    color: rgba(255,255,255,0.6);
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.2s ease;
}
.bottom-sheet-item:hover {
    background: rgba(242,101,34,0.08);
    border-color: rgba(242,101,34,0.2);
    color: var(--exl);
}

/* ── Desktop-only and Mobile-only visibility ── */
.desktop-only { display: block; }
.mobile-only { display: none; }
.tablet-only { display: none; }

/* ══════════════════════════════════════════════════════════════════════════
   iPAD / TABLET LAYOUT (769px - 1024px)
   Two-column: Leader avatar left, Chat right
   ══════════════════════════════════════════════════════════════════════════ */
@media screen and (min-width: 769px) and (max-width: 1024px) {
    .block-container { padding: 1rem !important; max-width: 100% !important; }
    
    /* Show tablet elements */
    .tablet-only { display: block !important; }
    
    /* Hide XP panel and badges on tablet - just leader + chat */
    .tablet-hide { display: none !important; }
    
    /* Hide the right sidebar (user avatar + scenarios) */
    [data-testid="column"]:last-child {
        display: none !important;
    }
    
    /* Two column layout: Leader (smaller) + Chat (larger) */
    [data-testid="column"]:first-child {
        flex: 0 0 200px !important;
        max-width: 200px !important;
    }
    [data-testid="column"]:nth-child(2) {
        flex: 1 1 auto !important;
        max-width: calc(100% - 220px) !important;
    }
    
    /* Compact leader avatar area */
    .avatar-ring { width: 120px !important; height: 120px !important; }
    .avatar-img { width: 110px !important; height: 110px !important; }
    
    /* Show FAB on tablet too */
    .use-cases-fab { display: flex !important; }
    
    /* Adjust chat container */
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
        height: calc(100vh - 140px) !important;
        max-height: calc(100vh - 140px) !important;
    }
}

/* ══════════════════════════════════════════════════════════════════════════
   MOBILE / PHONE LAYOUT (≤768px)
   Single column: Header + Chat only, no sidebars
   ══════════════════════════════════════════════════════════════════════════ */
@media screen and (max-width: 768px) {
    /* Full width, minimal padding */
    .block-container { 
        padding: 8px !important; 
        max-width: 100% !important;
        min-height: 100vh !important;
        height: auto !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
    
    /* Allow full page scroll on phone */
    .stApp { 
        overflow-y: auto !important; 
        -webkit-overflow-scrolling: touch !important;
    }
    
    /* Hide decorative orbs on mobile */
    .mobile-hide-orbs { display: none !important; }
    
    /* Show mobile-only elements */
    .mobile-only { display: block !important; }
    
    /* Phone-first header: avatar on top, chat-focused */
    .mobile-chat-header {
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        gap: 8px !important;
        padding: 10px 12px 8px !important;
        margin-bottom: 8px !important;
    }
    .mobile-chat-header .leader-avatar {
        width: 86px !important;
        height: 86px !important;
        border-width: 3px !important;
        box-shadow: 0 0 24px rgba(242,101,34,0.32) !important;
    }
    .mobile-chat-header .leader-info {
        flex: 0 0 auto !important;
    }
    .mobile-chat-header .leader-title {
        display: none !important;
    }
    .mobile-chat-header .switch-btn {
        padding: 8px 12px !important;
        font-size: 0.66rem !important;
    }

    /* Hide desktop-only elements */
    .desktop-only { display: none !important; }
    
    /* Hide ALL columns completely on phone */
    [data-testid="column"]:first-child,
    [data-testid="column"]:last-child {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }
    
    /* Make center chat column full width */
    [data-testid="column"]:nth-child(2) {
        flex: 1 1 100% !important;
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
    }
    
    /* Remove column gap */
    [data-testid="stHorizontalBlock"] {
        gap: 0 !important;
    }
    
    /* CRITICAL: Hide large avatar wrappers on phone */
    #leader-avatar-wrapper,
    #user-avatar-wrapper,
    .avatar-wrapper {
        display: none !important;
    }
    
    /* Hide XP panel, badges, use-cases section on phone */
    .tablet-hide,
    .use-cases-section {
        display: none !important;
    }
    
    /* Full height chat container */
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
        height: calc(100vh - 180px) !important;
        max-height: calc(100vh - 180px) !important;
        overflow-y: auto !important;
        border: none !important;
    }
    
    /* Hide Streamlit default padding */
    .stMarkdown { margin-bottom: 0.25rem !important; }
    
    /* Compact chat messages */
    [data-testid="stChatMessage"] {
        padding: 10px 12px !important;
        margin-bottom: 6px !important;
        border-radius: 12px !important;
    }
    
    /* Fix chat input at bottom */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        padding: 8px 12px 12px !important;
        background: #06060B !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
        z-index: 100 !important;
    }

    /* Keep phone clean: no extra FAB/sheet clutter */
    .use-cases-fab,
    .bottom-sheet,
    .bottom-sheet-overlay {
        display: none !important;
    }
    
    /* Compact buttons */
    .stButton > button {
        padding: 8px 14px !important;
        font-size: 0.75rem !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        padding: 10px 16px !important;
        font-size: 0.78rem !important;
    }
}

/* ══════════════════════════════════════════════════════════════════════════
   SMALL PHONE (≤480px)
   ══════════════════════════════════════════════════════════════════════════ */
@media screen and (max-width: 480px) {
    .block-container { padding: 4px !important; }
    
    /* Smaller text */
    h1 { font-size: 1.3rem !important; }
    h2 { font-size: 1.1rem !important; }
    p { font-size: 0.85rem !important; }
    
    /* Compact buttons */
    .stButton > button {
        padding: 6px 10px !important;
        font-size: 0.7rem !important;
        border-radius: 8px !important;
    }
    
    /* Hide non-essential decorative elements */
    .feature-chip { display: none !important; }
    
    /* Compact chat */
    [data-testid="stChatMessage"] {
        padding: 8px 10px !important;
        border-radius: 10px !important;
    }
    
    /* Smaller FAB */
    .use-cases-fab {
        width: 48px;
        height: 48px;
        font-size: 1.2rem;
        bottom: 70px;
        right: 10px;
    }
    
    /* Compact mobile header */
    .mobile-chat-header {
        padding: 10px 12px;
        gap: 10px;
        margin-bottom: 6px;
    }
    .mobile-chat-header .leader-avatar {
        width: 48px;
        height: 48px;
        border-width: 2px;
    }
    .mobile-chat-header .leader-name {
        font-size: 0.95rem;
    }
    .mobile-chat-header .leader-title {
        font-size: 0.65rem;
    }
    .mobile-chat-header .switch-btn {
        padding: 8px 12px;
        font-size: 0.65rem;
    }
    
    /* Adjust chat height for smaller phones */
    [data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
        height: calc(100vh - 150px) !important;
        max-height: calc(100vh - 150px) !important;
    }
}

/* ══════════════════════════════════════════════════════════════════════════
   TOUCH-FRIENDLY IMPROVEMENTS
   ══════════════════════════════════════════════════════════════════════════ */
@media (hover: none) and (pointer: coarse) {
    .stButton > button {
        min-height: 44px;
        min-width: 44px;
    }
    
    [data-testid="stChatInput"] textarea {
        font-size: 16px !important; /* Prevents iOS zoom on focus */
    }
    
    .bottom-sheet-item {
        min-height: 48px;
        display: flex;
        align-items: center;
    }
    
    .mobile-chat-header .switch-btn {
        min-height: 44px;
    }
}
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
        "last_user_tts_text": None,
        "last_leader_tts_text": None,
        "last_leader_audio_b64": None,
        "last_user_audio_b64": None,
        "user_name": "",
        "user_avatar_path": None,
        "user_original_photo": None,
        "user_generated_avatar": None,
        "who_speaking": None,
        "video_url": None,
        "is_mobile": False,
        "bottom_sheet_open": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def _inject_mobile_detection():
    """Inject JavaScript to detect mobile and communicate with Streamlit via query params."""
    st.markdown("""
    <script>
    (function() {
        const isMobile = window.innerWidth <= 768 || 
            /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // Add class to body for CSS targeting
        if (isMobile) {
            document.body.classList.add('mobile-view');
        } else {
            document.body.classList.remove('mobile-view');
        }
        
        // Store in sessionStorage for persistence
        sessionStorage.setItem('is_mobile', isMobile ? 'true' : 'false');
        
        // Update on resize
        window.addEventListener('resize', function() {
            const nowMobile = window.innerWidth <= 768;
            if (nowMobile) {
                document.body.classList.add('mobile-view');
            } else {
                document.body.classList.remove('mobile-view');
            }
            sessionStorage.setItem('is_mobile', nowMobile ? 'true' : 'false');
        });
    })();
    </script>
    """, unsafe_allow_html=True)


def _is_mobile_request() -> bool:
    """Check if current request is from mobile based on query params or user agent heuristics."""
    # Check query params first (set by JS)
    query_params = st.query_params
    if query_params.get("mobile") == "true":
        return True
    
    # Fallback: use a conservative heuristic based on common mobile patterns
    # This is set by the JS on page load, but we also check for touch capability
    return st.session_state.get("is_mobile", False)


def _clean_tts_text(text: str) -> str:
    """Strip markdown/special characters for clean TTS."""
    if not text:
        return ""
    t = text
    # Remove code blocks and inline code
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    # Convert markdown links to plain text
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)
    # Remove URLs
    t = re.sub(r"https?://\S+", " ", t)
    # Remove markdown bullets and blockquotes
    t = re.sub(r"^\s*[-*•]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*>\s+", "", t, flags=re.MULTILINE)
    # Remove common special characters used in markdown
    t = re.sub(r"[*_~#|<>]", " ", t)
    # Remove quotes
    t = re.sub(r'["\']', "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


@st.cache_data
def load_leaders():
    return load_all_leaders()

leaders = load_leaders()


# ---------------------------------------------------------------------------
# Consent screen
# ---------------------------------------------------------------------------
def _render_ambient_orbs():
    """Floating gradient orbs, particles, rings, streaks, and constellation background."""
    st.markdown(
        '<div style="position:fixed;top:0;left:0;width:100%;height:100%;overflow:hidden;pointer-events:none;z-index:0;">'

        # ── Gradient orbs ──
        '<div style="position:absolute;top:12%;left:8%;width:340px;height:340px;border-radius:50%;'
        'background:radial-gradient(circle,rgba(242,101,34,0.18),rgba(242,101,34,0.03) 70%,transparent);'
        'filter:blur(60px);animation:orbFloat1 18s ease-in-out infinite;"></div>'
        '<div style="position:absolute;top:55%;right:10%;width:280px;height:280px;border-radius:50%;'
        'background:radial-gradient(circle,rgba(139,92,246,0.15),rgba(139,92,246,0.02) 70%,transparent);'
        'filter:blur(50px);animation:orbFloat2 22s ease-in-out infinite;"></div>'
        '<div style="position:absolute;top:30%;right:25%;width:200px;height:200px;border-radius:50%;'
        'background:radial-gradient(circle,rgba(45,212,191,0.12),rgba(45,212,191,0.02) 70%,transparent);'
        'filter:blur(45px);animation:orbFloat3 15s ease-in-out infinite;"></div>'
        '<div style="position:absolute;bottom:15%;left:20%;width:250px;height:250px;border-radius:50%;'
        'background:radial-gradient(circle,rgba(251,191,36,0.1),rgba(251,191,36,0.02) 70%,transparent);'
        'filter:blur(55px);animation:orbFloat4 20s ease-in-out infinite;"></div>'
        '<div style="position:absolute;top:8%;right:15%;width:150px;height:150px;border-radius:50%;'
        'background:radial-gradient(circle,rgba(244,114,182,0.12),transparent 70%);'
        'filter:blur(40px);animation:orbFloat1 25s ease-in-out infinite reverse;"></div>'
        '<div style="position:absolute;bottom:30%;right:5%;width:180px;height:180px;border-radius:50%;'
        'background:radial-gradient(circle,rgba(59,130,246,0.1),transparent 70%);'
        'filter:blur(45px);animation:orbFloat3 28s ease-in-out infinite reverse;"></div>'

        # ── Animated rings (center decorative) ──
        '<div style="position:absolute;top:50%;left:50%;width:500px;height:500px;border-radius:50%;'
        'border:1px solid rgba(242,101,34,0.06);animation:ringPulse 6s ease-in-out infinite;"></div>'
        '<div style="position:absolute;top:50%;left:50%;width:350px;height:350px;border-radius:50%;'
        'border:1px dashed rgba(139,92,246,0.08);animation:ringRotate 30s linear infinite;"></div>'
        '<div style="position:absolute;top:50%;left:50%;width:450px;height:450px;border-radius:50%;'
        'border:1px dashed rgba(45,212,191,0.06);animation:ringRotateR 40s linear infinite;"></div>'
        '<div style="position:absolute;top:50%;left:50%;width:600px;height:600px;border-radius:50%;'
        'border:1px solid rgba(242,101,34,0.03);animation:ringPulse 8s ease-in-out infinite 2s;"></div>'

        # ── Diagonal light streaks ──
        '<div style="position:absolute;top:0;left:0;width:1px;height:200px;'
        'background:linear-gradient(180deg,transparent,rgba(242,101,34,0.3),transparent);'
        'transform:rotate(35deg);animation:streak 8s linear infinite 0s;"></div>'
        '<div style="position:absolute;top:20%;left:30%;width:1px;height:150px;'
        'background:linear-gradient(180deg,transparent,rgba(139,92,246,0.25),transparent);'
        'transform:rotate(35deg);animation:streak 12s linear infinite 3s;"></div>'
        '<div style="position:absolute;top:40%;left:60%;width:1px;height:180px;'
        'background:linear-gradient(180deg,transparent,rgba(45,212,191,0.2),transparent);'
        'transform:rotate(35deg);animation:streak 10s linear infinite 6s;"></div>'

        # ── Constellation dots ──
        '<div style="position:absolute;top:15%;left:25%;width:3px;height:3px;border-radius:50%;background:rgba(242,101,34,0.5);animation:constellationPulse 3s ease-in-out infinite;"></div>'
        '<div style="position:absolute;top:22%;left:32%;width:2px;height:2px;border-radius:50%;background:rgba(242,101,34,0.4);animation:constellationPulse 3s ease-in-out infinite 0.5s;"></div>'
        '<div style="position:absolute;top:18%;left:30%;width:2px;height:2px;border-radius:50%;background:rgba(242,101,34,0.3);animation:constellationPulse 3s ease-in-out infinite 1s;"></div>'
        '<div style="position:absolute;top:75%;right:20%;width:3px;height:3px;border-radius:50%;background:rgba(139,92,246,0.5);animation:constellationPulse 4s ease-in-out infinite;"></div>'
        '<div style="position:absolute;top:70%;right:25%;width:2px;height:2px;border-radius:50%;background:rgba(139,92,246,0.4);animation:constellationPulse 4s ease-in-out infinite 0.7s;"></div>'
        '<div style="position:absolute;top:78%;right:18%;width:2px;height:2px;border-radius:50%;background:rgba(139,92,246,0.3);animation:constellationPulse 4s ease-in-out infinite 1.4s;"></div>'
        '<div style="position:absolute;top:40%;left:80%;width:2px;height:2px;border-radius:50%;background:rgba(45,212,191,0.4);animation:constellationPulse 3.5s ease-in-out infinite 0.3s;"></div>'
        '<div style="position:absolute;top:35%;left:75%;width:3px;height:3px;border-radius:50%;background:rgba(45,212,191,0.5);animation:constellationPulse 3.5s ease-in-out infinite;"></div>'

        # ── Floating particles (rising) ──
        '<div style="position:absolute;top:20%;left:15%;width:4px;height:4px;border-radius:50%;background:rgba(242,101,34,0.6);animation:particleDrift 12s linear infinite;"></div>'
        '<div style="position:absolute;top:60%;left:70%;width:3px;height:3px;border-radius:50%;background:rgba(139,92,246,0.5);animation:particleDrift 16s linear infinite 3s;"></div>'
        '<div style="position:absolute;top:80%;left:40%;width:3px;height:3px;border-radius:50%;background:rgba(45,212,191,0.5);animation:particleDrift 14s linear infinite 6s;"></div>'
        '<div style="position:absolute;top:45%;left:85%;width:2px;height:2px;border-radius:50%;background:rgba(251,191,36,0.5);animation:particleDrift 18s linear infinite 2s;"></div>'
        '<div style="position:absolute;top:70%;left:25%;width:3px;height:3px;border-radius:50%;background:rgba(244,114,182,0.4);animation:particleDrift 15s linear infinite 8s;"></div>'
        '<div style="position:absolute;top:35%;left:55%;width:2px;height:2px;border-radius:50%;background:rgba(242,101,34,0.4);animation:particleDrift 20s linear infinite 4s;"></div>'
        '<div style="position:absolute;top:90%;left:10%;width:3px;height:3px;border-radius:50%;background:rgba(59,130,246,0.5);animation:particleDrift 17s linear infinite 1s;"></div>'
        '<div style="position:absolute;top:85%;left:60%;width:2px;height:2px;border-radius:50%;background:rgba(244,114,182,0.5);animation:particleDrift 13s linear infinite 5s;"></div>'
        '<div style="position:absolute;top:50%;left:5%;width:3px;height:3px;border-radius:50%;background:rgba(45,212,191,0.4);animation:particleDrift 19s linear infinite 7s;"></div>'
        '<div style="position:absolute;top:95%;left:90%;width:2px;height:2px;border-radius:50%;background:rgba(251,191,36,0.4);animation:particleDrift 11s linear infinite 9s;"></div>'

        # ── Floating decorative icons ──
        '<div style="position:absolute;top:20%;left:5%;font-size:1.4rem;animation:floatIcon 8s ease-in-out infinite;">&#x1F4A1;</div>'
        '<div style="position:absolute;top:65%;right:8%;font-size:1.2rem;animation:floatIcon 10s ease-in-out infinite 2s;">&#x1F680;</div>'
        '<div style="position:absolute;bottom:20%;left:12%;font-size:1.1rem;animation:floatIcon 9s ease-in-out infinite 4s;">&#x2728;</div>'
        '<div style="position:absolute;top:12%;right:30%;font-size:1rem;animation:floatIcon 11s ease-in-out infinite 1s;">&#x1F3AF;</div>'
        '<div style="position:absolute;bottom:35%;right:15%;font-size:1.3rem;animation:floatIcon 7s ease-in-out infinite 3s;">&#x1F451;</div>'

        # ── Subtle grid overlay ──
        '<div style="position:absolute;top:0;left:0;width:100%;height:100%;'
        'background-image:linear-gradient(rgba(255,255,255,0.012) 1px,transparent 1px),'
        'linear-gradient(90deg,rgba(255,255,255,0.012) 1px,transparent 1px);'
        'background-size:50px 50px;animation:gridScroll 20s linear infinite;"></div>'

        # ── Center spotlight ──
        '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:600px;height:600px;'
        'background:radial-gradient(circle,rgba(242,101,34,0.06),transparent 60%);"></div>'

        '</div>',
        unsafe_allow_html=True,
    )


def render_consent():
    _render_ambient_orbs()

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown("&nbsp;", unsafe_allow_html=True)
    _c1, center, _c2 = st.columns([1, 1.8, 1])
    with center:
        # Logo with enhanced glow
        st.markdown(
            f'<div style="text-align:center;animation:fadeInUp 0.8s ease-out;">'
            f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:70px;margin-bottom:20px;'
            f'filter:drop-shadow(0 0 50px rgba(242,101,34,0.5)) drop-shadow(0 0 100px rgba(242,101,34,0.2));" />'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Title + subtitle
        st.markdown(
            '<div style="text-align:center;animation:fadeInUp 1s ease-out 0.15s both;">'
            '<h1 style="font-family:Syne,sans-serif;font-size:2.6rem;font-weight:800;'
            'color:#F0F0F8;margin-bottom:6px;line-height:1.1;">Leadership AI</h1>'
            '<p style="font-size:0.78rem;color:rgba(255,255,255,0.3);letter-spacing:0.14em;'
            'text-transform:uppercase;font-weight:500;margin-bottom:12px;">'
            'AI Summit 2026 &middot; Gamified Leadership Conversations</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Feature chips
        st.markdown(
            '<div style="text-align:center;animation:fadeInUp 1.1s ease-out 0.3s both;margin-bottom:32px;">'
            '<div style="display:inline-flex;gap:10px;flex-wrap:wrap;justify-content:center;">'
            '<span style="padding:7px 16px;border-radius:100px;font-size:0.7rem;font-weight:600;'
            'letter-spacing:0.05em;text-transform:uppercase;'
            'background:rgba(242,101,34,0.08);border:1px solid rgba(242,101,34,0.18);color:rgba(255,255,255,0.5);">'
            '&#x1F3AE; Gamified</span>'
            '<span style="padding:7px 16px;border-radius:100px;font-size:0.7rem;font-weight:600;'
            'letter-spacing:0.05em;text-transform:uppercase;'
            'background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.18);color:rgba(255,255,255,0.5);">'
            '&#x1F916; AI Avatars</span>'
            '<span style="padding:7px 16px;border-radius:100px;font-size:0.7rem;font-weight:600;'
            'letter-spacing:0.05em;text-transform:uppercase;'
            'background:rgba(45,212,191,0.08);border:1px solid rgba(45,212,191,0.18);color:rgba(255,255,255,0.5);">'
            '&#x1F3A4; Voice Cloned</span>'
            '</div></div>',
            unsafe_allow_html=True,
        )

        # Glassmorphism disclaimer card (animated border)
        st.markdown(
            '<div style="animation:fadeInUp 1.2s ease-out 0.45s both; margin-bottom: 24px;">'
            '<div style="position:relative;border-radius:20px;padding:2px;">'
            '<div style="position:absolute;inset:0;border-radius:20px;'
            'background:linear-gradient(135deg,rgba(242,101,34,0.3),rgba(139,92,246,0.2),rgba(45,212,191,0.2),rgba(242,101,34,0.3));'
            'background-size:300% 300%;animation:cardBorderFlow 6s ease infinite;"></div>'
            '<div style="position:relative;background:rgba(6,6,11,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);'
            'border-radius:18px;padding:20px 24px;margin-bottom:20px;">'
            '<p style="margin:0;font-size:0.82rem;color:rgba(255,255,255,0.55);line-height:1.6;">'
            '<strong style="color:rgba(255,255,255,0.7);">Disclaimer:</strong> '
            'This experience features AI-simulated avatars inspired by leadership personas. '
            'Responses are generated by AI and <strong>do not represent the actual views, '
            'opinions, or statements</strong> of any real individual. '
            'This is a demonstration for the EXL AI Summit.</p>'
            '</div></div></div>',
            unsafe_allow_html=True,
        )

        if st.button("I Understand — Enter the Experience", use_container_width=True, type="primary"):
            st.session_state.show_consent = False
            st.rerun()

        # Subtle footer
        st.markdown(
            '<div style="text-align:center;margin-top:40px;animation:fadeInUp 1.3s ease-out 0.6s both;">'
            '<p style="font-size:0.6rem;color:rgba(255,255,255,0.15);letter-spacing:0.1em;text-transform:uppercase;">'
            'Powered by Gemini &middot; Built for EXL</p></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Photo setup screen
# ---------------------------------------------------------------------------
def _save_user_photo(photo_bytes: bytes, name: str) -> str:
    safe_name = "".join(c if c.isalnum() else "_" for c in name.strip().lower()) or "visitor"
    out_dir = Path("assets/visitors")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{safe_name}.png"
    out_path.write_bytes(photo_bytes)
    return str(out_path)


def render_photo_setup():
    _render_ambient_orbs()

    st.markdown("&nbsp;", unsafe_allow_html=True)
    _c1, center, _c2 = st.columns([1, 2, 1])
    with center:
        st.markdown(
            f'<div style="text-align:center;animation:fadeInUp 0.7s ease-out;">'
            f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:36px;margin-bottom:14px;'
            f'filter:drop-shadow(0 0 30px rgba(242,101,34,0.35));" />'
            f'<h1 style="font-family:Syne,sans-serif;font-size:2rem;font-weight:800;margin-bottom:4px;'
            f'background:linear-gradient(135deg,#F0F0F8,#F26522);-webkit-background-clip:text;'
            f'-webkit-text-fill-color:transparent;background-clip:text;">Create Your Avatar</h1>'
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
    _render_ambient_orbs()

    user_name = st.session_state.user_name
    greeting = f", {user_name}" if user_name and user_name != "You" else ""

    st.markdown(
        f'<div style="text-align:center;padding:12px 0 4px;animation:fadeInUp 0.7s ease-out;">'
        f'<img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:42px;margin-bottom:12px;'
        f'filter:drop-shadow(0 0 40px rgba(242,101,34,0.4));" />'
        f'<h1 style="font-family:Syne,sans-serif;font-size:2.2rem;font-weight:800;margin-bottom:4px;'
        f'background:linear-gradient(135deg,#F0F0F8 0%,#F26522 50%,#F0F0F8 100%);'
        f'background-size:300% 100%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
        f'background-clip:text;animation:shimmer 4s linear infinite;">Leadership AI</h1>'
        f'<div style="display:inline-flex;gap:8px;margin-top:6px;">'
        f'<span style="padding:4px 12px;border-radius:100px;font-size:0.65rem;font-weight:600;'
        f'letter-spacing:0.06em;text-transform:uppercase;'
        f'background:rgba(242,101,34,0.1);border:1px solid rgba(242,101,34,0.2);color:#F4943E;">'
        f'Choose Your Leader{greeting}</span>'
        f'<span style="padding:4px 12px;border-radius:100px;font-size:0.65rem;font-weight:600;'
        f'letter-spacing:0.06em;text-transform:uppercase;'
        f'background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.2);color:#A78BFA;">'
        f'Ask Anything</span>'
        f'<span style="padding:4px 12px;border-radius:100px;font-size:0.65rem;font-weight:600;'
        f'letter-spacing:0.06em;text-transform:uppercase;'
        f'background:rgba(45,212,191,0.1);border:1px solid rgba(45,212,191,0.2);color:#5EEAD4;">'
        f'Earn XP</span></div>'
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
                st.session_state.last_user_tts_text = None
                st.session_state.last_leader_tts_text = None
                st.session_state.last_leader_audio_b64 = None
                st.session_state.leaders_chatted_set.add(lid)
                st.session_state.video_url = None
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
def _render_mobile_chat_header(leader: dict, leader_avatar_b64: str):
    """Render compact mobile header with leader info and switch button."""
    leader_title = leader.get("title", "Leadership Advisor")
    
    st.markdown(
        f'''<div class="mobile-chat-header">
            <img class="leader-avatar" src="data:image/png;base64,{leader_avatar_b64}" alt="{leader["name"]}" />
            <div class="leader-info">
                <p class="leader-name">{leader["name"]}</p>
                <p class="leader-title">{leader_title}</p>
            </div>
            <button class="switch-btn" onclick="window.location.href='?switch=1'">Switch</button>
        </div>''',
        unsafe_allow_html=True,
    )


def _render_mobile_bottom_sheet(scenarios: list):
    """Render the mobile bottom sheet with use cases."""
    # Build category HTML
    categories_html = ""
    for i, cat in enumerate(scenarios):
        items_html = ""
        for item in cat["items"]:
            safe_prompt = item["prompt"].replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')
            items_html += f'''<button class="bottom-sheet-item" onclick="selectUseCase('{safe_prompt}')">{item["title"]}</button>'''
        
        categories_html += f'''
        <div class="bottom-sheet-category">
            <div class="bottom-sheet-category-header" onclick="toggleCategory({i})">
                <span class="icon">{cat["icon"]}</span>
                <span class="name">{cat["category"]}</span>
                <span class="arrow">›</span>
            </div>
            <div class="bottom-sheet-category-items" id="cat-items-{i}">
                {items_html}
            </div>
        </div>'''
    
    st.markdown(
        f'''
        <!-- Bottom Sheet Overlay -->
        <div class="bottom-sheet-overlay" id="bottomSheetOverlay" onclick="closeBottomSheet()"></div>
        
        <!-- Bottom Sheet -->
        <div class="bottom-sheet" id="bottomSheet">
            <div class="bottom-sheet-handle"></div>
            <div class="bottom-sheet-header">
                <h3>Use Cases</h3>
                <button class="bottom-sheet-close" onclick="closeBottomSheet()">&times;</button>
            </div>
            <div class="bottom-sheet-content">
                {categories_html}
            </div>
        </div>
        
        <!-- FAB Button -->
        <button class="use-cases-fab" id="useCasesFab" onclick="toggleBottomSheet()">📋</button>
        
        <script>
        function toggleBottomSheet() {{
            const sheet = document.getElementById('bottomSheet');
            const overlay = document.getElementById('bottomSheetOverlay');
            const fab = document.getElementById('useCasesFab');
            const isActive = sheet.classList.contains('active');
            
            if (isActive) {{
                sheet.classList.remove('active');
                overlay.classList.remove('active');
                fab.classList.remove('active');
            }} else {{
                sheet.classList.add('active');
                overlay.classList.add('active');
                fab.classList.add('active');
            }}
        }}
        
        function closeBottomSheet() {{
            document.getElementById('bottomSheet').classList.remove('active');
            document.getElementById('bottomSheetOverlay').classList.remove('active');
            document.getElementById('useCasesFab').classList.remove('active');
        }}
        
        function toggleCategory(index) {{
            const header = document.querySelectorAll('.bottom-sheet-category-header')[index];
            const items = document.getElementById('cat-items-' + index);
            
            header.classList.toggle('expanded');
            items.classList.toggle('expanded');
        }}
        
        function selectUseCase(prompt) {{
            // Close the bottom sheet
            closeBottomSheet();
            
            // Find the chat input and set the value
            const chatInput = document.querySelector('[data-testid="stChatInput"] textarea');
            if (chatInput) {{
                // Set the value
                chatInput.value = prompt;
                // Trigger input event
                chatInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                // Focus the input
                chatInput.focus();
            }}
        }}
        
        // Show FAB on mobile AND tablet (<=1024px), hide on desktop
        function checkMobile() {{
            const isMobileOrTablet = window.innerWidth <= 1024;
            const isMobile = window.innerWidth <= 768;
            const fab = document.getElementById('useCasesFab');
            const sheet = document.getElementById('bottomSheet');
            const overlay = document.getElementById('bottomSheetOverlay');
            
            // Show FAB on mobile and tablet
            if (fab) fab.style.display = isMobileOrTablet ? 'flex' : 'none';
            
            // Close sheet when switching to desktop
            if (!isMobileOrTablet && sheet) {{
                sheet.classList.remove('active');
                overlay.classList.remove('active');
            }}
        }}
        
        checkMobile();
        window.addEventListener('resize', checkMobile);
        </script>
        ''',
        unsafe_allow_html=True,
    )


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
            st.session_state.last_user_tts_text,
            st.session_state.last_leader_tts_text,
        )

    # Inject mobile detection
    _inject_mobile_detection()
    
    # Handle switch request from mobile header button
    if st.query_params.get("switch") == "1":
        st.query_params.clear()
        st.session_state.selected_leader = None
        st.session_state.tts_pending = False
        st.session_state.last_user_text = None
        st.session_state.last_leader_text = None
        st.session_state.last_user_tts_text = None
        st.session_state.last_leader_tts_text = None
        st.session_state.last_leader_audio_b64 = None
        st.session_state.who_speaking = None
        st.rerun()

    # Get leader avatar as base64 for mobile header
    leader_avatar_path = leader.get("avatar_image", "")
    if leader_avatar_path and Path(leader_avatar_path).exists():
        leader_avatar_b64 = base64.b64encode(Path(leader_avatar_path).read_bytes()).decode()
    else:
        leader_avatar_b64 = ""

    exchange_count = len([m for m in st.session_state.conversation if m["role"] == "user"])

    # ══════════════════════════════════════════════════════════════════════
    # MOBILE LAYOUT - Compact header + chat only (shown via CSS on mobile)
    # ══════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════
    # MOBILE HEADER - Shown only on phone via CSS (.mobile-only)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'''<div class="mobile-only" style="display:none;">
            <div class="mobile-chat-header">
                <img class="leader-avatar" src="data:image/png;base64,{leader_avatar_b64}" 
                     alt="{leader["name"]}" onerror="this.style.display='none'" />
                <div class="leader-info">
                    <p class="leader-name">{leader["name"]}</p>
                </div>
                <a href="?switch=1" class="switch-btn" style="text-decoration:none;">Switch</a>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )
    
    # Render bottom sheet for tablet only (hidden on phone via CSS)
    _render_mobile_bottom_sheet(get_scenarios())

    # ══════════════════════════════════════════════════════════════════════
    # DESKTOP/TABLET LAYOUT - 3-column layout (left/right hidden on phone via CSS)
    # ══════════════════════════════════════════════════════════════════════
    
    # Desktop top bar
    st.markdown(
        f'''<div class="desktop-only">
            <div style="display:flex;align-items:center;justify-content:space-between;
            padding:8px 18px;background:rgba(255,255,255,0.02);
            border:1px solid rgba(255,255,255,0.06);border-radius:12px;margin-bottom:10px;">
            <div style="display:flex;align-items:center;gap:10px;">
            <img src="data:image/png;base64,{EXL_LOGO_B64}" style="height:18px;opacity:0.7;" />
            <div style="width:1px;height:18px;background:rgba(255,255,255,0.08);"></div>
            <span style="font-family:Syne,sans-serif;font-size:0.78rem;font-weight:600;color:#F0F0F8;">
            Leadership AI</span>
            <div style="width:6px;height:6px;border-radius:50%;background:#4ADE80;
            box-shadow:0 0 6px rgba(74,222,128,0.5);animation:glowDot 2s ease-in-out infinite;"></div>
            </div>
            <span style="font-size:0.65rem;color:rgba(255,255,255,0.25);font-family:JetBrains Mono,monospace;">
            {exchange_count} exchanges</span></div>
        </div>''',
        unsafe_allow_html=True,
    )
    
    left_col, chat_col, right_col = st.columns([1.0, 2.9, 1.1], gap="large")

    # ══════════════════════════════════════════════════════════════════════
    # LEFT PANEL — Leader avatar (always) + XP + badges (desktop only, hidden on tablet)
    # ══════════════════════════════════════════════════════════════════════
    with left_col:
        # Leader avatar - visible on desktop AND tablet
        render_active_avatar(
            leader,
            is_speaking=False,
            video_url=st.session_state.video_url,
        )

        # XP panel, badges, switch button - hidden on tablet (tablet-hide class)
        st.markdown('<div class="tablet-hide">', unsafe_allow_html=True)
        
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
        st.markdown('</div>', unsafe_allow_html=True)

        # Switch button - always visible (desktop + tablet)
        if st.button("← Switch Leader", use_container_width=True, key="desktop_switch"):
            st.session_state.selected_leader = None
            st.session_state.tts_pending = False
            st.session_state.last_user_text = None
            st.session_state.last_leader_text = None
            st.session_state.last_user_tts_text = None
            st.session_state.last_leader_tts_text = None
            st.session_state.last_leader_audio_b64 = None
            st.session_state.who_speaking = None
            st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # RIGHT PANEL — User avatar + scenarios (desktop only)
    # ══════════════════════════════════════════════════════════════════════
    with right_col:
        st.markdown('<div class="desktop-only">', unsafe_allow_html=True)
        render_user_active_avatar(
            avatar_path=st.session_state.user_avatar_path,
            user_name=user_name,
            is_speaking=False,
        )

        st.markdown(
            '''<div class="use-cases-section">
                <div class="use-cases-title">
                    <span class="icon">💡</span>
                    <span class="text">Use Cases</span>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )

        scenarios_container = st.container(height=340)
        with scenarios_container:
            for cat in get_scenarios():
                with st.expander(f"{cat['icon']} {cat['category']}", expanded=False):
                    for item in cat["items"]:
                        if st.button(
                            item["title"],
                            key=f"sc_{cat['category'][:10]}_{item['title'][:20]}",
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
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # CENTER PANEL — Chat (visible on both mobile and desktop)
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
                user_audio_b64=st.session_state.last_user_audio_b64,
                has_video=bool(st.session_state.video_url),
            )

        user_input = st.chat_input(f"Ask {leader['name']} anything...")

        if st.session_state.pending_question:
            user_input = st.session_state.pending_question
            st.session_state.pending_question = None

        if user_input:
            st.session_state.who_speaking = "user"
            st.session_state.conversation.append({"role": "user", "content": user_input})
            st.session_state.video_url = None

            # 1. Render user message immediately INSIDE container
            with chat_container:
                render_chat_message(
                    "user",
                    user_input,
                    user_avatar_path=st.session_state.user_avatar_path
                )

                # 2. Show "thinking" loader INSIDE container
                leader_avatar = leader.get("avatar_image")
                if not leader_avatar or not Path(leader_avatar).exists():
                    leader_avatar = None
                
                with st.chat_message("assistant", avatar=leader_avatar):
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:12px;height:40px;">'
                        f'<div style="display:flex;">'
                        f'<div class="vibe-loader"></div>'
                        f'<div class="vibe-loader"></div>'
                        f'<div class="vibe-loader"></div>'
                        f'</div>'
                        f'<span style="font-size:0.75rem;color:rgba(255,255,255,0.4);font-style:italic;letter-spacing:0.05em;">'
                        f'{leader["name"].split()[0]} is thinking...</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

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
                st.session_state.last_user_tts_text = _clean_tts_text(user_input)
                st.session_state.last_leader_tts_text = _clean_tts_text(full_response)

                st.session_state.last_leader_audio_b64 = None
                st.session_state.last_user_audio_b64 = None

                # Generate user question audio (Edge TTS, free)
                user_audio = voice_client.synthesize_user_text(
                    st.session_state.last_user_tts_text
                )
                if user_audio:
                    st.session_state.last_user_audio_b64 = base64.b64encode(user_audio).decode()

                # Generate leader response audio (ElevenLabs → Edge TTS)
                audio_bytes = voice_client.synthesize_for_leader(
                    leader, st.session_state.last_leader_tts_text
                )
                if audio_bytes:
                    st.session_state.last_leader_audio_b64 = base64.b64encode(audio_bytes).decode()
                    
                    if voice_client.lipsync_available():
                        with st.spinner("Generating lip-sync video..."):
                            video_url = voice_client.generate_lip_sync(
                                audio_bytes,
                                leader.get("avatar_image", "")
                            )
                            if video_url:
                                st.session_state.video_url = video_url

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
