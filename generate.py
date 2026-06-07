#!/usr/bin/env python3
"""VibeVoice TTS with voice cloning — runs on GitHub Actions (16GB RAM)."""
import os, sys, json, time, subprocess, urllib.request

TEXT = os.environ.get("VOICE_TEXT", "Hello world.")
OUTPUT = os.environ.get("VOICE_OUTPUT", "vibevoice_output.wav")
MODEL_ID = os.environ.get("VOICE_MODEL", "microsoft/VibeVoice-Realtime-0.5B")
REF_AUDIO_URL = os.environ.get("VOICE_REF_URL", "")
VOICE_NAME = os.environ.get("VOICE_NAME", "en-Maya_woman")

print(f"Model: {MODEL_ID}")
print(f"Text: {TEXT[:100]}...")
print(f"Voice: {VOICE_NAME}")
if REF_AUDIO_URL:
    print(f"Reference: {REF_AUDIO_URL}")

start = time.time()

# ── Step 0: Download reference audio if provided ──
ref_audio_path = None
if REF_AUDIO_URL:
    ref_audio_path = "/tmp/reference_audio.wav"
    print(f"Downloading reference audio...")
    try:
        urllib.request.urlretrieve(REF_AUDIO_URL, ref_audio_path)
        # Convert to WAV 16kHz mono if needed
        subprocess.run([
            "ffmpeg", "-y", "-i", ref_audio_path, 
            "-ar", "16000", "-ac", "1", "-t", "30",
            "/tmp/reference_clean.wav"
        ], capture_output=True, timeout=30)
        ref_audio_path = "/tmp/reference_clean.wav"
        size = os.path.getsize(ref_audio_path)
        print(f"Reference audio: {size/1024:.0f}KB")
    except Exception as e:
        print(f"Reference download failed: {e}")
        ref_audio_path = None

# ── Approach 1: Try vibevoice pip package ──
try:
    print("Trying vibevoice package...")
    from vibevoice import Vibevoice
    vv = Vibevoice.from_pretrained(MODEL_ID)
    
    if ref_audio_path:
        audio = vv.generate(TEXT, voice=ref_audio_path)  # Clone from reference
    else:
        audio = vv.generate(TEXT, voice=VOICE_NAME)  # Preset voice
    
    import soundfile as sf
    sf.write(OUTPUT, audio, vv.sample_rate)
    print(f"✅ VibeVoice {'cloned' if ref_audio_path else 'preset'} in {time.time()-start:.0f}s")
    sys.exit(0)
except ImportError:
    print("vibevoice pip not available...")
except Exception as e:
    print(f"vibevoice failed: {e}")

# ── Approach 2: Community repo ──
try:
    print("Trying community VibeVoice repo...")
    sys.path.insert(0, '/tmp/vibevoice')
    from vibevoice import VibeVoice
    
    vv = VibeVoice.from_pretrained(MODEL_ID)
    if ref_audio_path:
        audio = vv.generate(TEXT, voice=ref_audio_path)
    else:
        audio = vv.generate(TEXT, voice=VOICE_NAME)
    
    import soundfile as sf
    sf.write(OUTPUT, audio, vv.sample_rate)
    print(f"✅ Community VibeVoice in {time.time()-start:.0f}s")
    sys.exit(0)
except Exception as e:
    print(f"Community VibeVoice failed: {e}")

# ── Approach 3: Edge TTS fallback ──
print("VibeVoice unavailable — edge-tts fallback...")
subprocess.run([
    "edge-tts", "--voice", "en-US-MichelleNeural", "--rate", "+5%",
    "--text", TEXT, "--write-media", OUTPUT
], check=True, timeout=60)
print(f"✅ edge-tts fallback in {time.time()-start:.0f}s")
print(f"Output: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f}KB)")
