#!/usr/bin/env python3
import os
import subprocess
import threading
import time

def test_backend():
    """Test Lambda functions with AWS resources"""
    print("1. Testing backend functions with AWS resources...")
    result = os.system("python3 test-local.py")
    return result == 0

def start_mock_api():
    """Start mock API server for backend"""
    print("2. Starting mock API server...")
    try:
        subprocess.Popen(["python3", "mock-api-server.py"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("✅ Mock API server started on http://localhost:5001")
        return True
    except Exception as e:
        print(f"❌ Failed to start mock API: {e}")
        return False

def start_frontend():
    """Start React frontend"""
    print("3. Starting frontend...")
    os.chdir("frontend-v2")
    print("Installing dependencies...")
    os.system("npm install")
    print("\n🚀 Starting React app on http://localhost:3000")
    print("\n📝 You can now:")
    print("   - Register a new account")
    print("   - Login with existing account")
    print("   - Test text-to-speech conversion")
    print("   - Check audio library")
    print("\n⚠️  Press Ctrl+C to stop")
    os.system("npm start")

if __name__ == "__main__":
    print("=== End-to-End Testing ===")
    print("Using existing AWS resources...\n")
    
    # Test backend first
    if test_backend():
        print("✅ Backend test passed\n")
    else:
        print("⚠️  Backend test had issues, but continuing...\n")
    
    # Start mock API in background
    start_mock_api()
    
    # Start frontend (this will block)
    start_frontend()