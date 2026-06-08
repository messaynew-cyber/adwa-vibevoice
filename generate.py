#!/usr/bin/env python3
"""Pocket TTS — CPU-native voice cloning. 100M params, 5s audio → clone any voice."""
import os, sys, time, subprocess, urllib.request, scipy.io.wavfile, torch

TEXT = os.environ.get("VOICE_TEXT", "Hello world.")
OUTPUT = os.environ.get("VOICE_OUTPUT", "pocket_output.wav")
REF_AUDIO_URL = os.environ.get("VOICE_REF_URL", "")

print(f"Text: {TEXT[:100]}...")
if REF_AUDIO_URL:
    print(f"Reference: {REF_AUDIO_URL}")

start = time.time()

# ── Download reference audio ──
ref_path = None
if REF_AUDIO_URL:
    try:
        ref_path = "/tmp/reference.wav"
        print(f"Downloading {REF_AUDIO_URL[:60]}...")
        urllib.request.urlretrieve(REF_AUDIO_URL, "/tmp/ref_raw")
        raw_size = os.path.getsize("/tmp/ref_raw")
        print(f"Raw: {raw_size/1024:.0f}KB")
        result = subprocess.run(["ffmpeg", "-y", "-i", "/tmp/ref_raw", "-ar", "16000", "-ac", "1", "-t", "10", ref_path], capture_output=True, timeout=30)
        if os.path.exists(ref_path):
            print(f"Reference ready: {os.path.getsize(ref_path)/1024:.0f}KB")
        else:
            print(f"ffmpeg failed: {result.stderr.decode()[:200]}")
            ref_path = None
    except Exception as e:
        print(f"Reference error: {e}")
        ref_path = None

# ── Pocket TTS ──
try:
    print("Loading Pocket TTS...")
    from pocket_tts import TTSModel
    
    model = TTSModel.load_model()
    print(f"Loaded in {time.time()-start:.0f}s")
    
    if ref_path and os.path.exists(ref_path):
        print("Cloning voice from reference...")
        voice_state = model.get_state_for_audio_prompt(ref_path)
    else:
        raise Exception("No reference audio available for cloning")
    
    gen_start = time.time()
    audio = model.generate_audio(voice_state, TEXT)
    
    scipy.io.wavfile.write(OUTPUT, model.sample_rate, audio.numpy())
    
    size_kb = os.path.getsize(OUTPUT) / 1024
    label = "CLONED" if ref_path else "GENERATED"
    print(f"✅ {label} VOICE in {time.time()-gen_start:.0f}s — {size_kb:.0f}KB")
    print(f"Total: {time.time()-start:.0f}s")
    sys.exit(0)
except Exception as e:
    print(f"Pocket TTS failed: {e}")

# ── Fallback ──
print("Pocket TTS unavailable — edge-tts fallback...")
subprocess.run(["edge-tts", "--voice", "en-US-MichelleNeural", "--rate", "+5%", "--text", TEXT, "--write-media", OUTPUT], check=True, timeout=60)
print(f"✅ edge-tts ({os.path.getsize(OUTPUT)/1024:.0f}KB)")
