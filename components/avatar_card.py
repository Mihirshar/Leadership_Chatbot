import json
import streamlit as st
import streamlit.components.v1 as components
from utils.helpers import get_image_base64, hex_to_rgba


def render_tts_dialogue(
    user_text: str,
    leader_text: str,
    leader_name: str = "Leader",
    leader_audio_b64: str | None = None,
):
    """Single hidden component: speaks the user question (fast), then leader response.

    If leader_audio_b64 (base64-encoded MP3 from ElevenLabs) is provided,
    the leader's reply is played with the cloned voice via <audio>.
    Otherwise falls back to browser speechSynthesis for both.
    """
    safe_user = json.dumps((user_text or "")[:400])
    safe_leader = json.dumps((leader_text or "")[:2000])
    
    # JavaScript to sync audio playback with UI animations
    js_logic = f"""
    <script>
    (function(){{
        var synth = window.parent.speechSynthesis || window.speechSynthesis;
        if (synth) synth.cancel();

        var userEl = window.parent.document.getElementById('user-avatar-wrapper');
        var leaderEl = window.parent.document.getElementById('leader-avatar-wrapper');

        function setSpeaking(el, speaking) {{
            if (!el) return;
            if (speaking) el.classList.add('speaking');
            else el.classList.remove('speaking');
        }}

        // Ensure clean state initially
        setSpeaking(userEl, false);
        setSpeaking(leaderEl, false);

        var uQ = new SpeechSynthesisUtterance({safe_user});
        uQ.rate = 1.25; uQ.pitch = 1.05; uQ.lang = 'en';

        uQ.onstart = function() {{ setSpeaking(userEl, true); }};
        uQ.onend = function() {{ 
            setSpeaking(userEl, false); 
            setTimeout(playLeader, 350); 
        }};

        function playLeader() {{
            setSpeaking(leaderEl, true);
            var audioData = "{leader_audio_b64 or ''}";
            
            if (audioData) {{
                var audio = new Audio("data:audio/mpeg;base64," + audioData);
                audio.onended = function() {{ setSpeaking(leaderEl, false); }};
                audio.play().catch(function(e) {{
                    console.error("Audio play failed, falling back to TTS", e);
                    fallbackTTS();
                }});
            }} else {{
                fallbackTTS();
            }}
        }}

        function fallbackTTS() {{
            if (!synth) return;
            var uA = new SpeechSynthesisUtterance({safe_leader});
            uA.rate = 0.95; uA.pitch = 0.88; uA.lang = 'en';
            uA.onstart = function() {{ setSpeaking(leaderEl, true); }};
            uA.onend = function() {{ setSpeaking(leaderEl, false); }};
            synth.speak(uA);
        }}

        if (synth && {safe_user}.length > 0) {{
            synth.speak(uQ);
        }} else {{
            playLeader();
        }}
    }})();
    </script>
    """
    components.html(js_logic, height=0)


def render_avatar_card(leader: dict) -> bool:
    accent = leader.get("accent_color", "#F26522")
    avatar_path = leader.get("avatar_image", "")
    b64 = get_image_base64(avatar_path)

    if b64:
        img_tag = f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
    else:
        img_tag = f'<span style="font-size:2.8rem;">{leader.get("emoji", "")}</span>'

    glow = hex_to_rgba(accent, 0.25)
    glow2 = hex_to_rgba(accent, 0.1)

    html = (
        f'<div style="text-align:center;padding:24px 16px 16px;'
        f'background:linear-gradient(145deg,{hex_to_rgba(accent, 0.04)},{hex_to_rgba(accent, 0.01)});'
        f'border:1px solid {hex_to_rgba(accent, 0.12)};border-radius:20px;position:relative;overflow:hidden;">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:3px;'
        f'background:linear-gradient(90deg,transparent,{accent},transparent);opacity:0.6;"></div>'
        f'<div style="width:120px;height:120px;border-radius:50%;border:3px solid {accent};'
        f'margin:0 auto 14px;overflow:hidden;box-shadow:0 0 25px {glow},0 0 50px {glow2};'
        f'animation:avatarFloat 3s ease-in-out infinite;">'
        f'{img_tag}</div>'
        f'<div style="display:flex;justify-content:center;align-items:center;gap:3px;height:18px;margin-bottom:14px;">'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};opacity:0.4;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};opacity:0.4;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};opacity:0.4;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};opacity:0.4;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};opacity:0.4;"></div>'
        f'</div>'
        f'<h3 style="margin:0 0 2px;font-family:Syne,sans-serif;font-size:1.15rem;font-weight:700;color:#F0F0F8;">{leader["name"]}</h3>'
        f'<p style="margin:0 0 12px;font-size:0.75rem;color:{accent};font-weight:600;text-transform:uppercase;letter-spacing:0.04em;">{leader["role"]}</p>'
        f'<p style="margin:0 4px;font-size:0.7rem;color:rgba(255,255,255,0.4);font-style:italic;line-height:1.45;">'
        f'&ldquo;{leader["personality"]["leadership_philosophy"]}&rdquo;</p>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)
    return st.button(
        f"Chat with {leader['name'].split()[0]}",
        key=f"select_{leader['id']}",
        use_container_width=True,
    )


def render_user_active_avatar(
    avatar_path: str | None,
    user_name: str,
    is_speaking: bool = False, # Ignored, controlled by JS
    speak_text: str | None = None,
):
    accent = "#F26522"
    b64 = get_image_base64(avatar_path) if avatar_path else ""
    
    if b64:
        img_tag = f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
    else:
        img_tag = '<span style="font-size:3rem;">&#x1F464;</span>'

    glow = hex_to_rgba(accent, 0.35)
    glow2 = hex_to_rgba(accent, 0.15)
    
    # ID is crucial for JS sync
    html = (
        f'<div id="user-avatar-wrapper" class="avatar-wrapper" style="text-align:center;padding:8px 0 12px;">'
        f'<div class="avatar-ring" style="width:220px;height:220px;border-radius:50%;border:4px solid {accent};'
        f'margin:0 auto 12px;overflow:hidden;'
        f'box-shadow:0 0 40px {glow},0 0 80px {glow2};">'
        f'{img_tag}</div>'
        f'<div style="display:flex;justify-content:center;align-items:center;gap:4px;height:24px;margin-bottom:12px;">'
        f'<div class="wave-bar" style="width:4px;height:20px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:20px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.12s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:20px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.24s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:20px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.36s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:20px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.48s;"></div>'
        f'</div>'
        f'<h2 style="margin:0 0 4px;font-family:Syne,sans-serif;font-size:1.4rem;font-weight:700;color:#F0F0F8;">{user_name}</h2>'
        f'<p class="status-text" style="margin:0;font-size:0.8rem;color:rgba(255,255,255,0.3);font-weight:500;text-transform:uppercase;letter-spacing:0.08em;"><span>LISTENING</span></p>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_active_avatar(
    leader: dict,
    is_speaking: bool = False, # Ignored, controlled by JS
    speak_text: str | None = None,
    video_url: str | None = None,
):
    accent = leader.get("accent_color", "#F26522")
    avatar_img = leader.get("avatar_image", "")
    b64 = get_image_base64(avatar_img)

    glow = hex_to_rgba(accent, 0.35)
    glow2 = hex_to_rgba(accent, 0.15)

    if video_url:
        img_tag = (
            f'<video src="{video_url}" autoplay playsinline '
            f'style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></video>'
        )
    elif b64:
        img_tag = (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
        )
    else:
        img_tag = f'<span style="font-size:3rem;">{leader.get("emoji", "")}</span>'

    html = (
        f'<div id="leader-avatar-wrapper" class="avatar-wrapper" style="text-align:center;padding:8px 0 12px;">'
        f'<div class="avatar-ring" style="width:220px;height:220px;border-radius:50%;border:4px solid {accent};'
        f'margin:0 auto 12px;overflow:hidden;'
        f'box-shadow:0 0 40px {glow},0 0 80px {glow2};">'
        f'{img_tag}</div>'
        f'<div style="display:flex;justify-content:center;align-items:center;gap:4px;height:24px;margin-bottom:12px;">'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.1s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.2s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.3s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.4s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.5s;"></div>'
        f'<div class="wave-bar" style="width:4px;height:22px;border-radius:3px;background:{accent};transform-origin:center;animation-delay:0.6s;"></div>'
        f'</div>'
        f'<h2 style="margin:0 0 4px;font-family:Syne,sans-serif;font-size:1.4rem;font-weight:700;color:#F0F0F8;">{leader["name"]}</h2>'
        f'<p style="margin:0 0 4px;font-size:0.85rem;color:{accent};font-weight:600;text-transform:uppercase;letter-spacing:0.06em;">{leader["role"]}</p>'
        f'<p class="status-text" style="margin:0;font-size:0.75rem;color:rgba(255,255,255,0.3);font-weight:500;text-transform:uppercase;letter-spacing:0.08em;"><span>LISTENING</span></p>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
