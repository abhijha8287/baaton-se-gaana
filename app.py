import base64
import io
import os

import streamlit as st
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

LANGUAGES = {
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Bengali": "bn-IN",
    "Marathi": "mr-IN",
    "Kannada": "kn-IN",
    "Malayalam": "ml-IN",
    "Gujarati": "gu-IN",
    "Punjabi": "pa-IN",
}
STYLES = ["Bollywood", "Rap", "Romantic", "Funny", "Sad", "Desi Folk"]
SPEAKERS = ["shubh", "anushka", "abhilash", "manisha"]  # tried in order

EXAMPLE_CONVO = (
    "Person 1: Bhai kal exam hai aur maine kuch nahi padha.\n"
    "Person 2: Tension mat le, raat ko dono milke padh lenge.\n"
    "Person 1: Par mujhe neend bahut aati hai yaar!\n"
    "Person 2: Chai banayenge, Maggi khayenge, aur topper banke dikhayenge!"
)


def sarvam():
    key = os.getenv("SARVAM_API_KEY")
    if not key:
        st.error("SARVAM_API_KEY missing. Add it to .env")
        st.stop()
    return SarvamAI(api_subscription_key=key)


MIME_TYPES = {"wav": "audio/wav", "mp3": "audio/mpeg", "m4a": "audio/x-m4a", "webm": "audio/webm"}


def transcribe(audio_bytes, filename, lang_code):
    client = sarvam()
    # Set the MIME type explicitly: Linux guesses audio/vnd.wave for .wav, which Sarvam rejects
    mime = MIME_TYPES.get(filename.rsplit(".", 1)[-1].lower(), "application/octet-stream")
    last_err = None
    for model in ("saaras:v3", None):
        try:
            kwargs = dict(file=(filename, audio_bytes, mime), language_code=lang_code)
            if model:
                kwargs["model"] = model
                kwargs["mode"] = "transcribe"
            resp = client.speech_to_text.transcribe(**kwargs)
            return resp.transcript
        except Exception as e:
            last_err = e
    raise last_err


def build_prompt(transcript, language, style):
    return f"""Here is a real conversation between two people:

\"\"\"{transcript}\"\"\"

Turn THIS conversation into a short, catchy {style} song in {language}.
Rules:
- First understand the story: who said what, the main situation, emotions, funny moments.
- Keep the specific details (names, places, things, plans, jokes) from the conversation. Do not write generic lyrics.
- Write 6 to 10 short, rhythmic lines with rhyme, like a real {style} song — not a summary.
- Write in {language} using its native script (Hinglish-style mixing is fine if the conversation mixes languages).
- Keep it short enough to be sung/spoken in about 30 seconds.
- Output ONLY the lyrics, one line per line. No title, no explanations, no notes."""


def generate_lyrics(transcript, language, style):
    prompt = build_prompt(transcript, language, style)
    system = "You are a hit Indian songwriter who turns everyday conversations into catchy songs."
    oa_key = os.getenv("OPENAI_API_KEY", "")
    if oa_key and oa_key != "your_key_here":
        try:
            from openai import OpenAI

            resp = OpenAI(api_key=oa_key).chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                temperature=0.9,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            st.warning(f"OpenAI failed ({e}); using Sarvam instead.")
    resp = sarvam().chat.completions(
        model="sarvam-105b",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        temperature=0.8,
        reasoning_effort="low",
        max_tokens=2000,
    )
    text = resp.choices[0].message.content or ""
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    return text.strip()


def text_to_song(lyrics, lang_code):
    client = sarvam()
    text = lyrics[:1500]
    last_err = None
    for model, speaker in [("bulbul:v3", s) for s in SPEAKERS] + [("bulbul:v2", "anushka")]:
        try:
            resp = client.text_to_speech.convert(
                text=text, language_code=lang_code, speaker=speaker, model=model, pace=0.95
            )
            return b"".join(base64.b64decode(a) for a in resp.audios)
        except Exception as e:
            last_err = e
    raise last_err


# ---------------- UI ----------------
st.set_page_config(page_title="Baaton Se Gaana", page_icon="🎵", layout="centered")
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #1a0b2e 0%, #3a1250 55%, #7a1d4f 100%); }
    h1, h2, h3, p, label, .stMarkdown { color: #fff !important; }
    .lyrics { background: rgba(255,255,255,0.08); border-left: 4px solid #ffb300;
              padding: 1rem 1.2rem; border-radius: 10px; font-size: 1.2rem; line-height: 1.9;
              color: #fff; white-space: pre-wrap; }
    .convo { background: rgba(0,0,0,0.25); padding: 0.8rem 1rem; border-radius: 10px;
             color: #eee; white-space: pre-wrap; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown("<h1 style='text-align:center'>🎵 Baaton Se Gaana</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;font-size:1.15rem'>Two people talk. AI turns their conversation into a song.</p>",
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)
language = c1.selectbox("Language", list(LANGUAGES))
style = c2.selectbox("Song style", STYLES)
lang_code = LANGUAGES[language]

st.markdown("### 🎤 Start Recording")
audio = None
filename = "recording.wav"
if hasattr(st, "audio_input"):
    rec = st.audio_input("🎤 Start Recording — tap the mic, talk, then stop")
    if rec is not None:
        audio, filename = rec.getvalue(), "recording.wav"
else:
    st.info("Recording not supported in this Streamlit version — upload audio instead.")

up = st.file_uploader("Upload conversation audio", type=["wav", "mp3", "m4a", "webm"])
if up is not None:
    audio, filename = up.getvalue(), up.name

if st.button("✨ Try this conversation (example)"):
    st.session_state.use_example = True
if audio is not None and st.session_state.get("use_example") and st.session_state.get("example_audio") != hash(audio):
    st.session_state.use_example = False  # new audio overrides example
st.session_state.example_audio = hash(audio) if audio is not None else None

transcript = None
if st.session_state.get("use_example"):
    transcript = EXAMPLE_CONVO
elif audio is not None:
    key = hash(audio)
    if st.session_state.get("audio_key") != key:
        with st.spinner("Listening to your conversation (Sarvam STT)..."):
            try:
                st.session_state.transcript = transcribe(audio, filename, lang_code)
                st.session_state.audio_key = key
                st.session_state.pop("song", None)
            except Exception as e:
                st.error(f"Sarvam speech-to-text failed: {e}")
                st.stop()
    transcript = st.session_state.get("transcript")

if transcript:
    st.markdown("### Conversation")
    st.markdown(f"<div class='convo'>{transcript}</div>", unsafe_allow_html=True)

    song_key = (transcript, language, style)
    if st.session_state.get("song_key") != song_key:
        with st.spinner(f"Writing your {style} song..."):
            try:
                lyrics = generate_lyrics(transcript, language, style)
            except Exception as e:
                st.error(f"Could not write lyrics: {e}")
                st.stop()
        song_audio, tts_err = None, None
        with st.spinner("Singing it (Sarvam TTS)..."):
            try:
                song_audio = text_to_song(lyrics, lang_code)
            except Exception as e:
                tts_err = str(e)
        st.session_state.song = (lyrics, song_audio, tts_err)
        st.session_state.song_key = song_key

    lyrics, song_audio, tts_err = st.session_state.song
    st.markdown("### 🎶 Your Song")
    if song_audio:
        st.markdown("**▶️ Play Song**")
        st.audio(song_audio, format="audio/wav")
    else:
        st.warning(f"Text-to-speech failed, but here are your lyrics: {tts_err}")
    st.markdown(f"<div class='lyrics'>{lyrics}</div>", unsafe_allow_html=True)
    if st.button("🔁 New version"):
        st.session_state.pop("song_key", None)
        st.rerun()
