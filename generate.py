#!/usr/bin/env python3
"""Coqui TTS with XTTS v2 voice cloning — GitHub Actions (16GB RAM, CPU)."""
import os, sys, time, subprocess, urllib.request, json

TEXT = os.environ.get("VOICE_TEXT", "Hello world.")
OUTPUT = os.environ.get("VOICE_OUTPUT", "coqui_output.wav")
REF_AUDIO_URL = os.environ.get("VOICE_REF_URL", "")

print(f"Text: {TEXT[:100]}...")
if REF_AUDIO_URL:
    print(f"Reference: {REF_AUDIO_URL}")

start = time.time()

# ── Step 0: Download reference audio ──
ref_path = None
if REF_AUDIO_URL:
    try:
        ref_path = "/tmp/reference.wav"
        urllib.request.urlretrieve(REF_AUDIO_URL, "/tmp/ref_raw")
        subprocess.run([
            "ffmpeg", "-y", "-i", "/tmp/ref_raw",
            "-ar", "22050", "-ac", "1", "-t", "15", ref_path
        ], capture_output=True, timeout=30)
        print(f"Reference ready: {os.path.getsize(ref_path)/1024:.0f}KB")
    except Exception as e:
        print(f"Reference download failed: {e}")
        ref_path = None

# ── Coqui TTS XTTS v2 ──
try:
    print("Loading Coqui TTS XTTS v2...")
    
    # Use the TTS API
    from TTS.api import TTS
    
    # Load XTTS v2 model
    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts = TTS(model_name=model_name, progress_bar=False)
    
    print(f"Model loaded in {time.time()-start:.0f}s. Generating...")
    
    gen_start = time.time()
    
    if ref_path:
        # Voice cloning: use reference audio as speaker
        tts.tts_to_file(
            text=TEXT,
            speaker_wav=ref_path,
            language="en",
            file_path=OUTPUT
        )
        print(f"✅ CLONED VOICE in {time.time()-gen_start:.0f}s")
    else:
        # Use a built-in voice
        tts.tts_to_file(text=TEXT, file_path=OUTPUT)
        print(f"✅ Generated in {time.time()-gen_start:.0f}s")
    
    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"Output: {OUTPUT} ({size_kb:.0f}KB)")
    print(f"Total time: {time.time()-start:.0f}s")
    sys.exit(0)
    
except Exception as e:
    print(f"Coqui TTS failed: {e}")

# ── Fallback: edge-tts ──
print("Coqui unavailable — edge-tts fallback...")
subprocess.run([
    "edge-tts", "--voice", "en-US-MichelleNeural", "--rate", "+5%",
    "--text", TEXT, "--write-media", OUTPUT
], check=True, timeout=60)
print(f"✅ edge-tts fallback")
print(f"Output: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f}KB)")
