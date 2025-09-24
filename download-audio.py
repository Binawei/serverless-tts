#!/usr/bin/env python3
"""
Download the generated audio file
"""

import boto3
import os

# Load credentials
def load_env():
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

load_env()

def download_audio():
    s3 = boto3.client('s3')
    bucket = 'tts-bucket-1758058711'
    reference_key = 'a35655df-166e-48e9-aca9-bd8abf56e413'
    
    audio_key = f'download/{reference_key}/Audio.mp3'
    local_file = 'generated-audio.mp3'
    
    try:
        s3.download_file(bucket, audio_key, local_file)
        print(f"✅ Audio downloaded: {local_file}")
        print(f"🎧 Play the file to hear your TTS conversion!")
        
        # Try to open with default audio player
        import subprocess
        import platform
        
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', local_file])
        elif platform.system() == 'Windows':
            subprocess.run(['start', local_file], shell=True)
        else:  # Linux
            subprocess.run(['xdg-open', local_file])
            
    except Exception as e:
        print(f"❌ Download error: {e}")

if __name__ == "__main__":
    download_audio()