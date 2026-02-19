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
    safe_name = json.dumps(leader_name)

    if leader_audio_b64:
        components.html(
            f"""<script>
(function(){{
  var synth = window.parent.speechSynthesis || window.speechSynthesis;
  if (synth) synth.cancel();

  var uQ = new SpeechSynthesisUtterance({safe_user});
  uQ.rate = 1.25; uQ.pitch = 1.05; uQ.lang = 'en';

  function playLeader(){{
    var audio = new Audio("data:audio/mpeg;base64,{leader_audio_b64}");
    audio.play().catch(function(e){{
      // autoplay blocked — fall back to speechSynthesis
      if (synth) {{
        var uA = new SpeechSynthesisUtterance({safe_leader});
        uA.rate = 0.95; uA.pitch = 0.88; uA.lang = 'en';
        synth.speak(uA);
      }}
    }});
  }}

  if (synth && {safe_user}.length > 0) {{
    uQ.onend = function(){{ setTimeout(playLeader, 350); }};
    synth.speak(uQ);
  }} else {{
    playLeader();
  }}
}})();
</script>""",
            height=0,
        )
    else:
        components.html(
            f"""<script>
(function(){{
  var synth = window.parent.speechSynthesis || window.speechSynthesis;
  if (!synth) return;
  synth.cancel();

  var uQ = new SpeechSynthesisUtterance({safe_user});
  uQ.rate = 1.25; uQ.pitch = 1.05; uQ.lang = 'en';

  var uA = new SpeechSynthesisUtterance({safe_leader});
  uA.rate = 0.95; uA.pitch = 0.88; uA.lang = 'en';

  uQ.onend = function(){{ setTimeout(function(){{ synth.speak(uA); }}, 350); }};
  synth.speak(uQ);
}})();
</script>""",
            height=0,
        )


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
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 1.2s ease-in-out infinite;animation-delay:0s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 1.2s ease-in-out infinite;animation-delay:0.15s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 1.2s ease-in-out infinite;animation-delay:0.3s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 1.2s ease-in-out infinite;animation-delay:0.45s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 1.2s ease-in-out infinite;animation-delay:0.6s;"></div>'
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


# ── Shared HTML/CSS for the TTS + lip-sync avatar component ──

def _wave_bars(accent: str, count: int = 7) -> str:
    return "".join(
        f'<div class="wb" style="animation-delay:{i * 0.09}s;background:{accent};"></div>'
        for i in range(count)
    )


def _speaking_avatar_html(
    img_b64: str,
    fallback_icon: str,
    name: str,
    subtitle: str,
    accent: str,
    speak_text: str,
    tts_rate: float = 1.0,
    tts_pitch: float = 1.0,
    tts_delay_ms: int = 0,
) -> str:
    glow = hex_to_rgba(accent, 0.35)
    glow2 = hex_to_rgba(accent, 0.15)

    if img_b64:
        img_tag = (
            f'<img id="avimg" src="data:image/png;base64,{img_b64}" '
            f'style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
        )
    else:
        img_tag = f'<span style="font-size:3rem;">{fallback_icon}</span>'

    safe_text = json.dumps(speak_text[:600])

    return f"""
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:transparent;overflow:hidden;font-family:'Inter',-apple-system,sans-serif;}}
#wrap{{text-align:center;padding:6px 0 10px;}}
#ring{{
    width:110px;height:110px;border-radius:50%;border:3px solid {accent};
    margin:0 auto 6px;overflow:hidden;
    box-shadow:0 0 25px {glow},0 0 50px {glow2};
    transition:box-shadow 0.3s,border-color 0.3s;
}}
#ring.talk{{
    border-color:#4ADE80;
    box-shadow:0 0 30px rgba(74,222,128,0.5),0 0 60px rgba(74,222,128,0.2);
    animation:glow 0.8s ease-in-out infinite alternate;
}}
@keyframes glow{{
    to{{box-shadow:0 0 45px rgba(74,222,128,0.65),0 0 80px rgba(74,222,128,0.3);}}
}}
#avimg.talk{{
    animation:lipSync 0.18s ease-in-out infinite alternate;
    transform-origin:center 68%;
}}
@keyframes lipSync{{
    0%{{transform:scale(1,1)}}
    100%{{transform:scale(0.997,1.012)}}
}}
#bars{{display:flex;justify-content:center;gap:3px;height:18px;margin-bottom:8px;}}
.wb{{
    width:3px;height:18px;border-radius:2px;transform-origin:center;
    transform:scaleY(0.2);transition:transform 0.08s;
}}
.wb.on{{animation:wave 0.55s ease-in-out infinite;}}
@keyframes wave{{
    0%,100%{{transform:scaleY(0.2)}}
    25%{{transform:scaleY(0.85)}}
    50%{{transform:scaleY(0.45)}}
    75%{{transform:scaleY(1)}}
}}
#nm{{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#F0F0F8;margin-bottom:2px;}}
#role{{font-size:0.65rem;color:{accent};font-weight:500;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:2px;}}
#st{{font-size:0.58rem;font-weight:500;text-transform:uppercase;letter-spacing:0.06em;
    color:rgba(255,255,255,0.3);transition:color 0.2s;}}
#st.talk{{color:#4ADE80;}}
</style>
<div id="wrap">
  <div id="ring">{img_tag}</div>
  <div id="bars">{_wave_bars(accent)}</div>
  <div id="nm">{name}</div>
  <div id="role">{subtitle}</div>
  <div id="st">Listening</div>
</div>
<script>
(function(){{
  const ring=document.getElementById('ring'),
        img=document.getElementById('avimg'),
        bars=document.querySelectorAll('.wb'),
        st=document.getElementById('st');
  function speak(){{
    const u=new SpeechSynthesisUtterance({safe_text});
    u.rate={tts_rate};u.pitch={tts_pitch};u.lang='en';
    u.onstart=function(){{
      ring.classList.add('talk');
      if(img)img.classList.add('talk');
      bars.forEach(function(b){{b.classList.add('on');}});
      st.textContent='Speaking';st.classList.add('talk');
    }};
    u.onend=function(){{
      ring.classList.remove('talk');
      if(img)img.classList.remove('talk');
      bars.forEach(function(b){{b.classList.remove('on');}});
      st.textContent='Done';st.classList.remove('talk');
    }};
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  }}
  setTimeout(speak,{tts_delay_ms});
}})();
</script>"""


def render_user_active_avatar(
    avatar_path: str | None,
    user_name: str,
    is_speaking: bool = False,
    speak_text: str | None = None,
):
    b64 = get_image_base64(avatar_path) if avatar_path else ""

    if speak_text:
        components.html(
            _speaking_avatar_html(
                img_b64=b64,
                fallback_icon="&#x1F464;",
                name=user_name,
                subtitle="You",
                accent="#F26522",
                speak_text=speak_text,
                tts_rate=1.15,
                tts_pitch=1.05,
            ),
            height=210,
        )
        return

    accent = "#F26522"
    if b64:
        img_tag = f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
    else:
        img_tag = '<span style="font-size:3rem;">&#x1F464;</span>'

    glow = hex_to_rgba(accent, 0.35)
    glow2 = hex_to_rgba(accent, 0.15)
    ring_anim = "speakingPulse 1s ease-in-out infinite" if is_speaking else "idlePulse 3s ease-in-out infinite"
    wave_opacity = "1" if is_speaking else "0.4"
    status_label = "Speaking" if is_speaking else "Listening"
    status_color = "#4ADE80" if is_speaking else "rgba(255,255,255,0.3)"

    html = (
        f'<div style="text-align:center;padding:8px 0 12px;">'
        f'<div style="width:110px;height:110px;border-radius:50%;border:3px solid {accent};'
        f'margin:0 auto 8px;overflow:hidden;'
        f'box-shadow:0 0 30px {glow},0 0 60px {glow2};animation:{ring_anim};">'
        f'{img_tag}</div>'
        f'<div style="display:flex;justify-content:center;align-items:center;gap:3px;height:18px;margin-bottom:10px;opacity:{wave_opacity};">'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.12s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.24s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.36s;"></div>'
        f'<div style="width:3px;height:16px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.48s;"></div>'
        f'</div>'
        f'<h2 style="margin:0 0 2px;font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:#F0F0F8;">{user_name}</h2>'
        f'<p style="margin:0;font-size:0.65rem;color:{status_color};font-weight:500;text-transform:uppercase;letter-spacing:0.06em;">{status_label}</p>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_active_avatar(
    leader: dict,
    is_speaking: bool = False,
    speak_text: str | None = None,
):
    accent = leader.get("accent_color", "#F26522")
    avatar_img = leader.get("avatar_image", "")
    b64 = get_image_base64(avatar_img)

    if speak_text:
        components.html(
            _speaking_avatar_html(
                img_b64=b64,
                fallback_icon=leader.get("emoji", ""),
                name=leader["name"],
                subtitle=leader["role"],
                accent=accent,
                speak_text=speak_text,
                tts_rate=0.95,
                tts_pitch=0.9,
                tts_delay_ms=0,
            ),
            height=210,
        )
        return

    glow = hex_to_rgba(accent, 0.35)
    glow2 = hex_to_rgba(accent, 0.15)

    if b64:
        img_tag = (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />'
        )
    else:
        img_tag = f'<span style="font-size:3rem;">{leader.get("emoji", "")}</span>'

    ring_anim = (
        "speakingPulse 1s ease-in-out infinite"
        if is_speaking
        else "idlePulse 3s ease-in-out infinite"
    )
    wave_opacity = "1" if is_speaking else "0.4"
    status_label = "Speaking" if is_speaking else "Listening"
    status_color = "#4ADE80" if is_speaking else "rgba(255,255,255,0.3)"

    html = (
        f'<div style="text-align:center;padding:8px 0 12px;">'
        f'<div style="width:110px;height:110px;border-radius:50%;border:3px solid {accent};'
        f'margin:0 auto 8px;overflow:hidden;'
        f'box-shadow:0 0 30px {glow},0 0 60px {glow2};animation:{ring_anim};">'
        f'{img_tag}</div>'
        f'<div style="display:flex;justify-content:center;align-items:center;gap:3px;height:18px;margin-bottom:10px;opacity:{wave_opacity};">'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0s;"></div>'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.1s;"></div>'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.2s;"></div>'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.3s;"></div>'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.4s;"></div>'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.5s;"></div>'
        f'<div style="width:3px;height:18px;border-radius:2px;background:{accent};transform-origin:center;animation:soundWave 0.8s ease-in-out infinite;animation-delay:0.6s;"></div>'
        f'</div>'
        f'<h2 style="margin:0 0 2px;font-family:Syne,sans-serif;font-size:1.1rem;font-weight:700;color:#F0F0F8;">{leader["name"]}</h2>'
        f'<p style="margin:0 0 2px;font-size:0.68rem;color:{accent};font-weight:500;text-transform:uppercase;letter-spacing:0.05em;">{leader["role"]}</p>'
        f'<p style="margin:0;font-size:0.6rem;color:{status_color};font-weight:500;text-transform:uppercase;letter-spacing:0.06em;">{status_label}</p>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
