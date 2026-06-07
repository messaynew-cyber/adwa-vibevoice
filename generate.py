#!/usr/bin/env python3
"""VibeVoice TTS — runs on GitHub Actions CPU (16GB RAM). Generates speech from text input."""
import os, sys, json, time

TEXT = os.environ.get("VOICE_TEXT", "Hello, I am Adwa. This is my new voice powered by VibeVoice.")
OUTPUT = os.environ.get("VOICE_OUTPUT", "vibevoice_output.wav")
MODEL_ID = os.environ.get("VOICE_MODEL", "microsoft/VibeVoice-Realtime-0.5B")

print(f"Model: {MODEL_ID}")
print(f"Text: {TEXT[:100]}...")
print(f"Output: {OUTPUT}")

start = time.time()

# ── Approach 1: Try vibevoice pip package ──
try:
    print("Trying vibevoice package...")
    from vibevoice import Vibevoice
    
    vv = Vibevoice.from_pretrained(MODEL_ID)
    audio = vv.generate(TEXT, voice="en-Maya_woman")
    
    import soundfile as sf
    sf.write(OUTPUT, audio, vv.sample_rate)
    print(f"✅ Generated via vibevoice package in {time.time()-start:.0f}s")
    print(f"Output: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f}KB)")
    sys.exit(0)
except ImportError:
    print("vibevoice package not available, trying transformers...")
except Exception as e:
    print(f"vibevoice package failed: {e}")

# ── Approach 2: Direct transformers ──
try:
    import torch
    from transformers import AutoModel, AutoProcessor
    import soundfile as sf
    
    print(f"Loading {MODEL_ID} on CPU...")
    device = "cpu"
    
    processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModel.from_pretrained(MODEL_ID, trust_remote_code=True).to(device)
    model.eval()
    
    print(f"Model loaded in {time.time()-start:.0f}s. Generating...")
    
    with torch.no_grad():
        # VibeVoice expects text with speaker annotation
        inputs = processor(text=f"[en-Maya_woman]{TEXT}", return_tensors="pt").to(device)
        outputs = model.generate(**inputs, max_new_tokens=2048)
        audio = processor.decode(outputs[0])
    
    sf.write(OUTPUT, audio.numpy().squeeze(), 24000)
    print(f"✅ Generated via transformers in {time.time()-start:.0f}s")
    print(f"Output: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f}KB)")
    sys.exit(0)
except Exception as e:
    print(f"Transformers approach failed: {e}")

# ── Approach 3: Edge TTS fallback (always works) ──
print("VibeVoice unavailable — falling back to edge-tts...")
import subprocess
subprocess.run([
    "edge-tts", "--voice", "en-US-MichelleNeural", "--rate", "+5%",
    "--text", TEXT, "--write-media", OUTPUT
], check=True, timeout=60)
print(f"✅ Generated via edge-tts fallback")
print(f"Output: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f}KB)")
