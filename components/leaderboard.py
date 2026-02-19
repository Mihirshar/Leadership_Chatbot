import streamlit as st
from core.personality_engine import check_badges, get_xp_level


def render_xp_panel(xp: int, questions_asked: int, leaders_chatted: int, total_leaders: int):
    level, title, next_threshold = get_xp_level(xp)
    prev_thresholds = [0, 100, 300, 600, 1000, 1500]
    current_base = prev_thresholds[min(level, len(prev_thresholds) - 1)]
    progress = (xp - current_base) / max(next_threshold - current_base, 1)
    progress = min(max(progress, 0.0), 1.0)

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-family:Syne,sans-serif;font-size:0.8rem;font-weight:700;color:#F0F0F8;">LEVEL {level}</span>'
        f'<span style="font-size:0.7rem;color:rgba(255,255,255,0.5);background:rgba(255,255,255,0.06);padding:2px 10px;border-radius:20px;">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.progress(progress)

    st.markdown(
        f'<div style="display:flex;justify-content:space-between;font-size:0.7rem;color:rgba(255,255,255,0.35);margin-top:-8px;margin-bottom:12px;">'
        f'<span>{xp} XP</span><span>{next_threshold} XP</span></div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.metric(label="Questions", value=questions_asked)
    with c2:
        st.metric(label="Leaders", value=leaders_chatted)


def render_badges(questions_asked: int, leaders_chatted: int, total_leaders: int):
    earned = check_badges(questions_asked, leaders_chatted, total_leaders)

    if not earned:
        st.caption("_Ask your first question to earn a badge!_")
        return

    for badge in earned:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;'
            f'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
            f'border-radius:10px;margin-bottom:6px;">'
            f'<span style="font-size:1.2rem;">{badge["icon"]}</span>'
            f'<div><div style="font-size:0.78rem;font-weight:600;color:#F0F0F8;">{badge["name"]}</div>'
            f'<div style="font-size:0.62rem;color:rgba(255,255,255,0.4);">{badge["description"]}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_insight_card(insight: str, leader_name: str, accent: str = "#F26522"):
    from utils.helpers import hex_to_rgba

    bg = hex_to_rgba(accent, 0.08)
    border = hex_to_rgba(accent, 0.2)

    st.markdown(
        f'<div style="background:{bg};border:1px solid {border};border-radius:14px;padding:16px;margin:12px 0;">'
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">'
        f'<span style="font-size:1rem;">&#x1F4A1;</span>'
        f'<span style="font-family:Syne,sans-serif;font-size:0.72rem;font-weight:700;color:{accent};text-transform:uppercase;letter-spacing:0.05em;">Key Insight from {leader_name}</span>'
        f'</div>'
        f'<p style="margin:0;font-size:0.82rem;color:#E8E8F0;line-height:1.5;font-style:italic;">&ldquo;{insight}&rdquo;</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
