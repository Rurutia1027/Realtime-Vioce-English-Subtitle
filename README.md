# Live Pronunciation Caption

A lightweight local tool for real-time English speech captions in a floating, always-on-top window.

## Why I built this

For non-native speakers, pronunciation practice often means:

- recording a video
- replaying it
- noticing mistakes too late
- repeating the whole loop again

That feedback loop is slow.  
Most real-time speaking/coaching tools in the market are also paid.

So I built this small **Live Caption** tool: speak and see your words immediately on screen while recording.

## What it does

- Captures microphone input in real time
- Transcribes spoken English text locally
- Shows one live caption line in a compact floating window
- Keeps the window always on top for recording workflows

## Key features

- Local-first usage (no ChatGPT login, no token billing)
- Minimal UI focused on speaking practice
- Automatic fallback recorder if the primary STT backend fails
- Tuned segmentation for longer sentence chunks

## Run

```bash
python3 live_caption_overlay.py
```

## Requirements

- Python 3.10+
- Microphone access permission
- Recommended packages:

```bash
python3 -m pip install RealtimeSTT sounddevice faster-whisper
```

If your machine has `PyAudio` / `portaudio` compatibility issues, the script automatically falls back to a `sounddevice + faster-whisper` path.

## Notes

- First run can be slower because speech models may download.
- Accuracy depends on microphone quality, environment noise, and speaking pace.
- This project is designed for fast feedback during pronunciation/video practice, not full ASR benchmarking.
