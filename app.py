from __future__ import annotations

import html
import time

import requests
import streamlit as st

from agent import Agent, EventKind, TOOLS

st.set_page_config(
    page_title="Nova AI — Local Chat",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Design system ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
  --bg:#080b12;
  --surface:#0d111a;
  --surface2:#121824;
  --surface3:#171e2b;
  --line:#222b3c;
  --text:#eef2f8;
  --muted:#8792a7;
  --accent:#7c5cff;
  --accent2:#21d4fd;
  --success:#47e6a1;
  --danger:#ff6b81;
}

html, body, [class*="css"] {
  font-family:'DM Sans', sans-serif !important;
  color:var(--text) !important;
  background:var(--bg) !important;
}
.stApp {
  background:
    radial-gradient(circle at 70% 0%, rgba(124,92,255,.13), transparent 28rem),
    radial-gradient(circle at 10% 30%, rgba(33,212,253,.07), transparent 25rem),
    var(--bg);
}
.main .block-container { max-width:1180px; padding:28px 34px 130px; }

[data-testid="stSidebar"] {
  background:rgba(9,12,18,.96) !important;
  border-right:1px solid var(--line);
}
[data-testid="stSidebar"] > div { padding-top:24px; }

.brand { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
.brand-icon {
  width:42px;height:42px;border-radius:14px;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--accent),var(--accent2)); color:white;
  font-family:'Space Grotesk'; font-weight:700; font-size:21px;
  box-shadow:0 8px 30px rgba(124,92,255,.25);
}
.brand-name { font-family:'Space Grotesk'; font-size:21px; font-weight:700; letter-spacing:-.5px; }
.brand-sub { color:var(--muted); font-size:12px; margin-left:54px; margin-top:-5px; }

.hero { text-align:center; padding:52px 10px 30px; }
.hero-icon {
  width:66px;height:66px;border-radius:22px;margin:0 auto 18px;
  display:flex;align-items:center;justify-content:center;font-size:30px;
  background:linear-gradient(135deg,rgba(124,92,255,.2),rgba(33,212,253,.14));
  border:1px solid rgba(124,92,255,.35);
}
.hero h1 { font-family:'Space Grotesk'; font-size:42px; margin:0 0 10px; letter-spacing:-1.7px; }
.hero p { color:var(--muted); margin:0 auto; max-width:650px; font-size:15px; line-height:1.6; }

.status {
  display:inline-flex;align-items:center;gap:7px;margin-top:18px;padding:7px 12px;
  border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.025);
  font-size:12px;color:var(--muted);
}
.status-dot { width:7px;height:7px;border-radius:50%;background:var(--success); box-shadow:0 0 12px var(--success); }

.card {
  background:rgba(18,24,36,.72); border:1px solid var(--line); border-radius:18px;
  padding:18px; margin:10px 0;
}
.card-title { font-family:'Space Grotesk'; font-weight:600; margin-bottom:7px; }
.card-sub { color:var(--muted); font-size:12px; line-height:1.55; }

.feature-grid { display:grid;grid-template-columns:repeat(2,1fr);gap:12px;max-width:850px;margin:20px auto; }
.feature {
  text-align:left;background:rgba(18,24,36,.6);border:1px solid var(--line);border-radius:16px;
  padding:16px; transition:.2s;
}
.feature:hover { border-color:rgba(124,92,255,.55); transform:translateY(-1px); }
.feature-icon { font-size:19px;margin-bottom:8px; }
.feature-title { font-weight:600;font-size:14px; }
.feature-text { color:var(--muted);font-size:12px;margin-top:4px;line-height:1.45; }

.chat-row { display:flex; gap:12px; margin:22px 0; }
.chat-row.user { justify-content:flex-end; }
.avatar {
  width:34px;height:34px;border-radius:12px;flex:0 0 34px;display:flex;align-items:center;justify-content:center;
  background:var(--surface3);border:1px solid var(--line);font-size:14px;font-weight:700;
}
.avatar.ai { background:linear-gradient(135deg,var(--accent),#4b8cff); border:0; }
.bubble {
  max-width:78%;padding:13px 16px;border-radius:17px;border:1px solid var(--line);
  background:rgba(18,24,36,.8);line-height:1.65;font-size:14px;white-space:pre-wrap;
}
.user .bubble { background:linear-gradient(135deg,rgba(124,92,255,.18),rgba(124,92,255,.08)); border-color:rgba(124,92,255,.28); }

.tool {
  margin:6px 0 6px 46px;padding:10px 13px;border:1px solid var(--line);border-radius:12px;
  background:rgba(13,17,26,.7);color:var(--muted);font-size:12px;
}
.tool b { color:var(--accent2); }

[data-testid="stChatInput"] {
  position:fixed; bottom:18px; left:50%; transform:translateX(-50%); width:min(850px, calc(100vw - 40px));
  z-index:1000;
}
[data-testid="stChatInput"] > div {
  background:rgba(13,17,26,.94) !important; border:1px solid #303b50 !important;
  border-radius:18px !important; box-shadow:0 12px 50px rgba(0,0,0,.45);
  backdrop-filter:blur(14px);
}
[data-testid="stChatInput"] textarea { color:var(--text) !important; font-size:14px !important; }
.stButton button {
  border:1px solid var(--line) !important;background:var(--surface2) !important;color:var(--text) !important;
  border-radius:11px !important; font-weight:500 !important;
}
.stButton button:hover { border-color:var(--accent) !important; color:white !important; }
div[data-baseweb="select"] > div, .stSlider > div { background:var(--surface2) !important; }
.stCaption, small { color:var(--muted) !important; }
hr { border-color:var(--line) !important; }
footer { visibility:hidden; }

@media (max-width: 700px) {
  .main .block-container { padding:18px 14px 120px; }
  .hero { padding-top:25px; }
  .hero h1 { font-size:32px; }
  .feature-grid { grid-template-columns:1fr; }
  .bubble { max-width:88%; }
}
</style>
""",
    unsafe_allow_html=True,
)


def get_models() -> list[str]:
    try:
        response = requests.get("ollama launch claude", timeout=3)
        if response.ok:
            models = [m.get("name") for m in response.json().get("models", []) if m.get("name")]
            if models:
                return models
    except requests.RequestException:
        pass
    return ["llama3.2", "mistral", "gemma3", "qwen2.5"]


def ollama_online() -> bool:
    try:
        return requests.get("http://localhost:11434/api/tags", timeout=2).ok
    except requests.RequestException:
        return False


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


# ---------- State ----------
defaults = {
    "history": [],
    "turns": [],
    "total_steps": 0,
    "total_time": 0.0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-icon">✦</div><div class="brand-name">Nova AI</div></div>'
        '<div class="brand-sub">LOCAL INTELLIGENCE • OLLAMA</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    models = get_models()
    model = st.selectbox("MODEL", models, index=0)
    temperature = st.slider("CREATIVITY", 0.0, 1.0, 0.4, 0.05)
    max_steps = st.slider("MAX TOOL STEPS", 2, 16, 8)

    st.markdown("### Tools")
    for name, info in TOOLS.items():
        st.markdown(
            f'<div style="padding:6px 0;color:#8792a7;font-size:12px">'
            f'<span style="color:#21d4fd">{info["icon"]}</span>&nbsp; {name.replace("_"," ").title()}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    status = "Online" if ollama_online() else "Offline"
    dot = "var(--success)" if status == "Online" else "var(--danger)"
    st.markdown(
        f'<div style="font-size:12px;color:var(--muted)">'
        f'<span style="color:{dot}">●</span>&nbsp; Ollama {status}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("New chat", use_container_width=True):
            st.session_state.history = []
            st.session_state.turns = []
            st.session_state.total_steps = 0
            st.session_state.total_time = 0.0
            st.rerun()
    with c2:
        st.caption(f"{len(st.session_state.turns)} chats")

    st.divider()
    st.markdown(
        f'<div style="font-size:11px;color:var(--muted);line-height:1.8">'
        f'Model&nbsp;&nbsp;<b style="color:#eef2f8">{esc(model)}</b><br>'
        f'Tool calls&nbsp;&nbsp;<b style="color:#eef2f8">{st.session_state.total_steps}</b><br>'
        f'Time&nbsp;&nbsp;<b style="color:#eef2f8">{st.session_state.total_time:.1f}s</b>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------- Main ----------
if not st.session_state.turns:
    online = ollama_online()
    status_text = "Ollama connected" if online else "Ollama not detected"
    st.markdown(
        f"""
        <section class="hero">
          <div class="hero-icon">✦</div>
          <h1>Meet Nova AI</h1>
          <p>A redesigned local-first chatbot with streaming responses, intelligent tool use,
          conversation memory, and a clean modern interface.</p>
          <div class="status"><span class="status-dot" style="background:{'var(--success)' if online else 'var(--danger)'}"></span>{status_text}</div>
        </section>
        <div class="feature-grid">
          <div class="feature"><div class="feature-icon">⚡</div><div class="feature-title">Fast local AI</div><div class="feature-text">Run supported Ollama models directly on your machine.</div></div>
          <div class="feature"><div class="feature-icon">⌁</div><div class="feature-title">Smart tools</div><div class="feature-text">Calculator, date/time, Wikipedia and URL fetching built in.</div></div>
          <div class="feature"><div class="feature-icon">◌</div><div class="feature-title">Conversation memory</div><div class="feature-text">Keep context across messages during the current session.</div></div>
          <div class="feature"><div class="feature-icon">◈</div><div class="feature-title">Developer friendly</div><div class="feature-text">Simple Python architecture that is easy to extend with RAG or agents.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="display:flex;align-items:center;justify-content:space-between;margin:8px 0 24px">'
        '<div><div style="font-family:Space Grotesk;font-size:25px;font-weight:700">Nova AI</div>'
        '<div style="color:var(--muted);font-size:12px">Local assistant · ready to help</div></div>'
        '<div style="font-size:11px;color:var(--muted);border:1px solid var(--line);padding:6px 10px;border-radius:999px">✦ '
        + esc(model) + "</div></div>",
        unsafe_allow_html=True,
    )


def render_turn(turn: dict):
    user = esc(turn["user"])
    st.markdown(
        f'<div class="chat-row user"><div class="bubble">{user}</div><div class="avatar">Y</div></div>',
        unsafe_allow_html=True,
    )
    for event in turn.get("events", []):
        if event["kind"] == EventKind.TOOL_CALL:
            st.markdown(
                f'<div class="tool">⚙ <b>Using {esc(event["meta"].get("tool","tool"))}</b>'
                f' · {esc(event["content"])}</div>',
                unsafe_allow_html=True,
            )
        elif event["kind"] == EventKind.FINAL:
            st.markdown(
                f'<div class="chat-row"><div class="avatar ai">✦</div><div class="bubble">{event["content"]}</div></div>',
                unsafe_allow_html=True,
            )
        elif event["kind"] == EventKind.ERROR:
            st.error(event["content"])


for turn in st.session_state.turns:
    render_turn(turn)


# ---------- Input ----------
if prompt := st.chat_input("Message Nova AI…"):
    st.markdown(
        f'<div class="chat-row user"><div class="bubble">{esc(prompt)}</div><div class="avatar">Y</div></div>',
        unsafe_allow_html=True,
    )

    agent = Agent(model=model, temperature=temperature, max_steps=max_steps)
    final_ph = st.empty()
    status_ph = st.empty()
    final_text = ""
    saved_events = []
    step_count = 0
    started = time.time()

    status_ph.markdown(
        '<div class="tool">✦ <b>Nova is thinking</b> · working locally…</div>',
        unsafe_allow_html=True,
    )

    for event in agent.run(prompt, history=st.session_state.history):
        if event.kind == EventKind.TOOL_CALL:
            step_count += 1
            saved_events.append({
                "kind": EventKind.TOOL_CALL,
                "content": event.content,
                "meta": event.meta,
            })
            status_ph.markdown(
                f'<div class="tool">⚙ <b>Using {esc(event.meta.get("tool","tool"))}</b>'
                f' · {esc(event.content)}</div>',
                unsafe_allow_html=True,
            )
        elif event.kind == EventKind.TOOL_RESULT:
            saved_events.append({
                "kind": EventKind.TOOL_RESULT,
                "content": event.content,
                "meta": event.meta,
            })
        elif event.kind == EventKind.FINAL:
            final_text += event.content
            final_ph.markdown(
                f'<div class="chat-row"><div class="avatar ai">✦</div>'
                f'<div class="bubble">{final_text}▌</div></div>',
                unsafe_allow_html=True,
            )
        elif event.kind == EventKind.ERROR:
            status_ph.empty()
            st.error(event.content)
            saved_events.append({"kind": EventKind.ERROR, "content": event.content})
        elif event.kind == EventKind.DONE:
            step_count = event.meta.get("steps", step_count)

    status_ph.empty()
    final_ph.markdown(
        f'<div class="chat-row"><div class="avatar ai">✦</div><div class="bubble">{final_text}</div></div>',
        unsafe_allow_html=True,
    )

    elapsed = round(time.time() - started, 2)
    st.session_state.turns.append({
        "user": prompt,
        "events": saved_events + ([{"kind": EventKind.FINAL, "content": final_text}] if final_text else []),
        "stats": {"steps": step_count, "elapsed": elapsed, "model": model},
    })
    st.session_state.history.append({"role": "user", "content": prompt})
    st.session_state.history.append({"role": "assistant", "content": final_text or "(no final answer)"})
    st.session_state.total_steps += step_count
    st.session_state.total_time += elapsed
