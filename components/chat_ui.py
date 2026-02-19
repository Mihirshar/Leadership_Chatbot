import streamlit as st
from pathlib import Path


def render_chat_message(
    role: str,
    content: str,
    leader: dict | None = None,
    user_avatar_path: str | None = None,
):
    if role == "user":
        avatar = user_avatar_path if user_avatar_path and Path(user_avatar_path).exists() else None
        with st.chat_message("user", avatar=avatar):
            st.markdown(content)
    else:
        avatar_path = leader.get("avatar_image", "") if leader else None
        avatar = avatar_path if avatar_path and Path(avatar_path).exists() else None
        with st.chat_message("assistant", avatar=avatar):
            st.markdown(content)


def render_welcome_message(leader: dict, user_name: str = ""):
    accent = leader.get("accent_color", "#F26522")
    greeting = f"Welcome, {user_name}!" if user_name and user_name != "You" else "Welcome."
    st.markdown(
        f'<div style="text-align:center;padding:36px 16px;">'
        f'<div style="width:40px;height:40px;border-radius:50%;border:2px solid rgba(242,101,34,0.3);'
        f'margin:0 auto 14px;display:flex;align-items:center;justify-content:center;'
        f'background:rgba(242,101,34,0.06);font-size:1.2rem;">&#x1F4AC;</div>'
        f'<h3 style="font-family:Syne,sans-serif;font-size:1.15rem;color:#F0F0F8;margin:0 0 8px;font-weight:700;">'
        f'{greeting} {leader["name"]} is ready.</h3>'
        f'<p style="font-size:0.82rem;color:rgba(255,255,255,0.4);max-width:420px;margin:0 auto;line-height:1.55;">'
        f'Ask about leadership, strategy, culture, or organizational challenges. Every question earns you XP.</p>'
        f'<div style="margin:18px auto 0;width:40px;height:2px;background:linear-gradient(90deg,transparent,{accent},transparent);border-radius:2px;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
