# 🎵 Baaton Se Gaana

**Two people talk. AI turns their conversation into a song.**

🚀 **Live demo:** https://baaton-se-gaana-by-abhishek.streamlit.app/

Record a conversation in an Indian language. The app transcribes it with Sarvam AI, writes a short song from what was actually said (names, plans, jokes, feelings), and plays it back with Sarvam AI text-to-speech.

```
Record conversation → Sarvam STT → transcript → song lyrics → Sarvam TTS → play
```

## Features

- 🎤 Record in the browser, or upload audio (wav, mp3, m4a, webm)
- 🌏 9 languages: Hindi, Tamil, Telugu, Bengali, Marathi, Kannada, Malayalam, Gujarati, Punjabi
- 🎶 6 song styles: Bollywood, Rap, Romantic, Funny, Sad, Desi Folk
- ✨ A "Try this conversation" button that runs an example without recording
- 🔁 A button to write a new version of the song
- If text-to-speech fails, the lyrics are still shown

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/abhijha8287/baaton-se-gaana.git
cd baaton-se-gaana
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create a `.env` file:

```env
SARVAM_API_KEY=your_sarvam_key
OPENAI_API_KEY=your_openai_key   # optional
```

- `SARVAM_API_KEY` (required): get one at [dashboard.sarvam.ai](https://dashboard.sarvam.ai).
- `OPENAI_API_KEY` (optional): if set, `gpt-4o-mini` writes the lyrics. Otherwise Sarvam's `sarvam-105b` chat model is used. Set `OPENAI_MODEL` to use a different OpenAI model.

## Run

```bash
.venv/bin/streamlit run app.py
```

Open http://localhost:8501, pick a language and style, then record or upload a conversation.

## Demo tips

- `samples/example_conversation_hindi.wav` is a short Hindi conversation. Upload it if the mic isn't available.
- `samples/example_song.wav` is an example of the output.
- The "✨ Try this conversation" button skips speech-to-text and uses a built-in example.

## How it works

| Step | Service |
|------|---------|
| Speech → text | Sarvam `speech_to_text.transcribe` (`saaras:v3`) |
| Transcript → lyrics | OpenAI `gpt-4o-mini`, or Sarvam `sarvam-105b` |
| Lyrics → audio | Sarvam `text_to_speech.convert` (`bulbul:v3`, falls back to `bulbul:v2`) |

The lyrics prompt asks for the story and specific details from the conversation, so the song matches what was said rather than being generic.

The voice speaks the lyrics rather than singing them.
