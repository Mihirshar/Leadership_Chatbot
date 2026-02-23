import json
import streamlit as st
import streamlit.components.v1 as components
from utils.helpers import get_image_base64, hex_to_rgba


def render_tts_dialogue(
    user_text: str,
    leader_text: str,
    leader_name: str = "Leader",
    leader_audio_b64: str | None = None,
    user_audio_b64: str | None = None,
    has_video: bool = False,
):
    """Single hidden component: speaks the user question, then leader response.

    Both user and leader audio can be server-generated (Edge TTS / ElevenLabs).
    Falls back to browser speechSynthesis only if no audio bytes are available.
    
    On mobile devices, always shows a play button since autoplay is blocked.
    """
    safe_user = json.dumps((user_text or "")[:400])
    safe_leader = json.dumps((leader_text or "")[:2000])
    use_video = "true" if has_video else "false"
    has_user_audio = "true" if user_audio_b64 else "false"
    has_leader_audio = "true" if leader_audio_b64 else "false"
    
    js_logic = f"""
    <script>
    (function(){{
        var synth = window.parent.speechSynthesis || window.speechSynthesis;
        if (synth) synth.cancel();

        var userEl = window.parent.document.getElementById('user-avatar-wrapper');
        var leaderEl = window.parent.document.getElementById('leader-avatar-wrapper');
        var leaderVideo = window.parent.document.getElementById('leader-video');
        var hasVideo = {use_video};
        var hasUserAudio = {has_user_audio};
        var hasLeaderAudio = {has_leader_audio};
        
        // Detect mobile/touch devices
        var isMobile = ('ontouchstart' in window) || 
                       (navigator.maxTouchPoints > 0) || 
                       (window.innerWidth <= 768);
        
        // Track active audio to prevent overlapping
        var currentAudio = null;

        function setSpeaking(el, speaking) {{
            if (!el) return;
            if (speaking) el.classList.add('speaking');
            else el.classList.remove('speaking');
        }}
        
        function stopCurrentAudio() {{
            if (currentAudio) {{
                currentAudio.pause();
                currentAudio.currentTime = 0;
                currentAudio = null;
            }}
            if (synth) synth.cancel();
            setSpeaking(userEl, false);
            setSpeaking(leaderEl, false);
        }}

        function showPlayButton(targetEl, retryFn, label) {{
            if (!targetEl) return;
            var existing = targetEl.querySelector('.audio-retry-btn');
            if (existing) existing.remove();

            var btn = document.createElement('div');
            btn.className = 'audio-retry-btn';
            btn.innerHTML = label || '🔊 Tap to Listen';
            btn.style.cssText = 'position:absolute;bottom:20px;left:50%;transform:translateX(-50%);' +
                'background:linear-gradient(135deg,#F26522,#E85D26);color:white;' +
                'padding:12px 24px;border-radius:25px;font-size:14px;font-weight:600;' +
                'cursor:pointer;z-index:100;' +
                'box-shadow:0 4px 20px rgba(242,101,34,0.5),0 0 40px rgba(242,101,34,0.2);' +
                'border:2px solid rgba(255,255,255,0.3);' +
                'animation:fadeIn 0.3s ease-out,idlePulse 2s ease-in-out infinite;' +
                'text-shadow:0 1px 2px rgba(0,0,0,0.3);';
            
            // Use both click and touchend for mobile compatibility
            function handleTap(e) {{
                e.stopPropagation();
                e.preventDefault();
                stopCurrentAudio();
                retryFn();
                btn.remove();
            }}
            
            btn.addEventListener('click', handleTap);
            btn.addEventListener('touchend', handleTap);
            
            if (getComputedStyle(targetEl).position === 'static') {{
                targetEl.style.position = 'relative';
            }}
            targetEl.appendChild(btn);
        }}

        setSpeaking(userEl, false);
        setSpeaking(leaderEl, false);
        if (leaderVideo) {{
            leaderVideo.pause();
            leaderVideo.currentTime = 0;
            leaderVideo.muted = true;
        }}

        function playUser() {{
            if (hasUserAudio) {{
                var userAudio = new Audio("data:audio/mpeg;base64,{user_audio_b64 or ''}");
                currentAudio = userAudio;
                userAudio.onplay = function() {{ setSpeaking(userEl, true); }};
                userAudio.onended = function() {{
                    setSpeaking(userEl, false);
                    currentAudio = null;
                    setTimeout(playLeader, 350);
                }};
                userAudio.onerror = function() {{
                    setSpeaking(userEl, false);
                    currentAudio = null;
                    setTimeout(playLeader, 350);
                }};
                var p = userAudio.play();
                if (p !== undefined) {{
                    p.catch(function(e) {{
                        console.warn("User audio autoplay blocked", e);
                        setSpeaking(userEl, false);
                        currentAudio = null;
                        // On mobile, skip to leader audio with play button
                        if (isMobile) {{
                            showPlayButton(leaderEl, playLeaderWithInteraction, '🔊 Tap to Play Response');
                        }} else {{
                            showPlayButton(userEl, function() {{
                                setSpeaking(userEl, true);
                                currentAudio = userAudio;
                                userAudio.play();
                            }}, '🔊 Tap to Hear Question');
                        }}
                    }});
                }}
            }} else if (synth && {safe_user}.length > 0 && !isMobile) {{
                // Only use speechSynthesis on desktop
                var uQ = new SpeechSynthesisUtterance({safe_user});
                uQ.rate = 1.25; uQ.pitch = 1.05; uQ.lang = 'en';
                uQ.onstart = function() {{ setSpeaking(userEl, true); }};
                uQ.onend = function() {{
                    setSpeaking(userEl, false);
                    setTimeout(playLeader, 350);
                }};
                uQ.onerror = function() {{
                    setSpeaking(userEl, false);
                    setTimeout(playLeader, 350);
                }};
                synth.speak(uQ);
            }} else {{
                playLeader();
            }}
        }}
        
        function playLeaderWithInteraction() {{
            // Called after user interaction, so autoplay should work
            setSpeaking(leaderEl, true);
            
            if (hasVideo && leaderVideo) {{
                leaderVideo.muted = false;
                leaderVideo.currentTime = 0;
                leaderVideo.play().catch(function(e) {{
                    console.warn("Video play failed even after interaction", e);
                    setSpeaking(leaderEl, false);
                }});
                leaderVideo.onended = function() {{ setSpeaking(leaderEl, false); }};
                return;
            }}

            var audioData = "{leader_audio_b64 or ''}";
            if (audioData) {{
                var audio = new Audio("data:audio/mpeg;base64," + audioData);
                currentAudio = audio;
                audio.onended = function() {{ 
                    setSpeaking(leaderEl, false); 
                    currentAudio = null;
                }};
                audio.onerror = function() {{
                    setSpeaking(leaderEl, false);
                    currentAudio = null;
                }};
                audio.play().catch(function(e) {{
                    console.warn("Leader audio failed even after interaction", e);
                    setSpeaking(leaderEl, false);
                    currentAudio = null;
                }});
            }} else {{
                fallbackTTS();
            }}
        }}

        function playLeader() {{
            setSpeaking(leaderEl, true);
            
            if (hasVideo && leaderVideo) {{
                leaderVideo.muted = false;
                leaderVideo.currentTime = 0;
                var promise = leaderVideo.play();
                if (promise !== undefined) {{
                    promise.catch(function(e) {{
                        console.warn("Video autoplay blocked", e);
                        setSpeaking(leaderEl, false);
                        showPlayButton(leaderEl, playLeaderWithInteraction, '🔊 Tap to Play Response');
                    }});
                }}
                leaderVideo.onended = function() {{ setSpeaking(leaderEl, false); }};
                return;
            }}

            var audioData = "{leader_audio_b64 or ''}";
            if (audioData) {{
                var audio = new Audio("data:audio/mpeg;base64," + audioData);
                currentAudio = audio;
                audio.onended = function() {{ 
                    setSpeaking(leaderEl, false); 
                    currentAudio = null;
                }};
                audio.onerror = function() {{
                    setSpeaking(leaderEl, false);
                    currentAudio = null;
                }};
                var promise = audio.play();
                if (promise !== undefined) {{
                    promise.catch(function(e) {{
                        console.warn("Leader audio autoplay blocked", e);
                        setSpeaking(leaderEl, false);
                        currentAudio = null;
                        showPlayButton(leaderEl, playLeaderWithInteraction, '🔊 Tap to Play Response');
                    }});
                }}
            }} else {{
                fallbackTTS();
            }}
        }}

        function fallbackTTS() {{
            if (!synth || isMobile) {{
                // speechSynthesis often doesn't work well on mobile
                setSpeaking(leaderEl, false);
                return;
            }}
            var uA = new SpeechSynthesisUtterance({safe_leader});
            uA.rate = 0.95; uA.pitch = 0.88; uA.lang = 'en';
            uA.onstart = function() {{ setSpeaking(leaderEl, true); }};
            uA.onend = function() {{ setSpeaking(leaderEl, false); }};
            synth.speak(uA);
        }}

        // On mobile, always show play button immediately
        if (isMobile && (hasUserAudio || hasLeaderAudio || hasVideo)) {{
            showPlayButton(leaderEl, function() {{
                if (hasUserAudio) {{
                    playUser();
                }} else {{
                    playLeaderWithInteraction();
                }}
            }}, '🔊 Tap to Play Audio');
        }} else {{
            playUser();
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
        img_tag = f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;object-position:center top;border-radius:50%;" />'
    else:
        img_tag = f'<span style="font-size:2.8rem;">{leader.get("emoji", "")}</span>'

    glow = hex_to_rgba(accent, 0.25)
    glow2 = hex_to_rgba(accent, 0.1)

    html = (
        f'<div style="text-align:center;padding:24px 16px 16px;'
        f'background:linear-gradient(145deg,{hex_to_rgba(accent, 0.04)},{hex_to_rgba(accent, 0.01)});'
        f'border:1px solid {hex_to_rgba(accent, 0.12)};border-radius:20px;position:relative;overflow:hidden;'
        f'display:flex;flex-direction:column;min-height:410px;">'
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
        f'<h3 style="margin:0 0 2px;min-height:64px;display:flex;align-items:center;justify-content:center;'
        f'font-family:Syne,sans-serif;font-size:1.15rem;font-weight:700;color:#F0F0F8;">{leader["name"]}</h3>'
        f'<p style="margin:0 0 12px;min-height:36px;display:flex;align-items:center;justify-content:center;'
        f'font-size:0.75rem;color:{accent};font-weight:600;text-transform:uppercase;letter-spacing:0.04em;">{leader["role"]}</p>'
        f'<p style="margin:0 4px;min-height:78px;font-size:0.7rem;color:rgba(255,255,255,0.4);font-style:italic;line-height:1.45;">'
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
        img_tag = f'<img src="data:image/png;base64,{b64}" style="width:100%;height:100%;object-fit:cover;object-position:center top;border-radius:50%;" />'
    else:
        img_tag = '<span style="font-size:3rem;">&#x1F464;</span>'

    glow = hex_to_rgba(accent, 0.35)
    glow2 = hex_to_rgba(accent, 0.15)
    
    # ID is crucial for JS sync
    # Use max-width and responsive sizing for mobile
    html = (
        f'<div id="user-avatar-wrapper" class="avatar-wrapper" style="text-align:center;padding:8px 0 12px;">'
        f'<div class="avatar-ring" style="width:min(220px, 100%);height:min(220px, 100%);border-radius:50%;border:4px solid {accent};'
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
        # Added id="leader-video" for JS targeting
        img_tag = (
            f'<video id="leader-video" src="{video_url}" playsinline '
            f'style="width:100%;height:100%;object-fit:cover;border-radius:50%;"></video>'
        )
    elif b64:
        img_tag = (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="width:100%;height:100%;object-fit:cover;object-position:center top;border-radius:50%;" />'
        )
    else:
        img_tag = f'<span style="font-size:3rem;">{leader.get("emoji", "")}</span>'

    # Use max-width and responsive sizing for mobile
    html = (
        f'<div id="leader-avatar-wrapper" class="avatar-wrapper" style="text-align:center;padding:8px 0 12px;">'
        f'<div class="avatar-ring" style="width:min(220px, 100%);height:min(220px, 100%);border-radius:50%;border:4px solid {accent};'
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
