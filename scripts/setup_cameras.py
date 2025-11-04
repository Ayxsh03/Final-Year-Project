#!/usr/bin/env python3
"""
Camera Setup Script
This script helps you configure and test CCTV camera connections
"""

import cv2
import requests
import time
import argparse
from typing import List, Dict
import os

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = os.getenv("API_KEY", "111-1111-1-11-1-11-1-1")

def test_rtsp_connection(rtsp_url: str, timeout: int = 10) -> bool:
    """Test if RTSP URL is accessible"""
    print(f"Testing RTSP connection: {rtsp_url}")
    
    try:
        cap = cv2.VideoCapture(rtsp_url)
        
        # Set timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if ret:
                print("✅ RTSP connection successful!")
                cap.release()
                return True
            time.sleep(0.1)
        
        print("❌ RTSP connection failed - no frames received")
        cap.release()
        return False
        
    except Exception as e:
        print(f"❌ RTSP connection error: {e}")
        return False

def add_camera_to_db(name: str, rtsp_url: str, location: str) -> bool:
    """Add camera to database via API"""
    try:
        camera_data = {
            "name": name,
            "rtsp_url": rtsp_url,
            "location": location,
            "status": "offline"
        }
        
        # First, get existing cameras to check for duplicates
        response = requests.get(f"{API_BASE_URL}/cameras")
        if response.status_code == 200:
            existing_cameras = response.json()
            for camera in existing_cameras:
                if camera['name'] == name:
                    print(f"⚠️  Camera '{name}' already exists in database")
                    return False
        
        # Add new camera
        resp = requests.post(
            f"{API_BASE_URL}/cameras",
            json=camera_data,
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"}
        )
        if resp.status_code in (200, 201):
            created = resp.json()
            print(f"✅ Camera '{name}' added with id {created.get('id')}")
            return True
        else:
            print(f"❌ Failed to add camera: {resp.status_code} {resp.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error adding camera to database: {e}")
        return False

def discover_camera_settings():
    """Help discover camera RTSP URLs"""
    print("\n🔍 Camera Discovery Guide")
    print("=" * 50)
    
    common_patterns = [
        {
            "brand": "Hikvision",
            "pattern": "rtsp://username:password@camera_ip:554/Streaming/Channels/101",
            "example": "rtsp://admin:password123@192.168.1.100:554/Streaming/Channels/101"
        },
        {
            "brand": "Dahua", 
            "pattern": "rtsp://username:password@camera_ip:554/cam/realmonitor?channel=1&subtype=0",
            "example": "rtsp://admin:password123@192.168.1.100:554/cam/realmonitor?channel=1&subtype=0"
        },
        {
            "brand": "Axis",
            "pattern": "rtsp://username:password@camera_ip:554/axis-media/media.amp",
            "example": "rtsp://admin:password123@192.168.1.100:554/axis-media/media.amp"
        },
        {
            "brand": "Generic/ONVIF",
            "pattern": "rtsp://username:password@camera_ip:554/stream1",
            "example": "rtsp://admin:password123@192.168.1.100:554/stream1"
        }
    ]
    
    for pattern in common_patterns:
        print(f"\n{pattern['brand']}:")
        print(f"  Pattern: {pattern['pattern']}")
        print(f"  Example: {pattern['example']}")
    
    print(f"\n💡 Tips:")
    print(f"  - Replace 'camera_ip' with your camera's IP address")
    print(f"  - Use your camera's username/password")
    print(f"  - Default ports: 554 (RTSP), 80 (HTTP), 443 (HTTPS)")
    print(f"  - Check camera manual for specific RTSP paths")

def scan_network_cameras(network_base: str = "192.168.1") -> List[str]:
    """Scan network for potential camera IPs"""
    print(f"\n🔍 Scanning network {network_base}.x for cameras...")
    potential_cameras = []
    
    # This is a basic example - you might want to use nmap or similar tools
    for i in range(1, 255):
        ip = f"{network_base}.{i}"
        # Basic ping test (simplified)
        import subprocess
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                potential_cameras.append(ip)
        except:
            continue
    
    print(f"Found {len(potential_cameras)} responding IPs")
    return potential_cameras

def interactive_setup():
    """Interactive camera setup"""
    print("\n🎯 Interactive Camera Setup")
    print("=" * 50)
    
    cameras = []
    
    while True:
        print(f"\nCamera #{len(cameras) + 1}")
        name = input("Camera name (or 'done' to finish): ").strip()
        
        if name.lower() == 'done':
            break
            
        location = input("Location: ").strip()
        
        print("\nRTSP URL options:")
        print("1. Enter manually")
        print("2. Use pattern helper")
        
        choice = input("Choose option (1-2): ").strip()
        
        if choice == "2":
            discover_camera_settings()
            
        rtsp_url = input("\nEnter RTSP URL: ").strip()
        
        # Test connection
        if test_rtsp_connection(rtsp_url):
            cameras.append({
                "name": name,
                "rtsp_url": rtsp_url,
                "location": location
            })
            print(f"✅ Camera '{name}' added successfully!")
        else:
            retry = input("Connection failed. Add anyway? (y/N): ").strip().lower()
            if retry == 'y':
                cameras.append({
                    "name": name,
                    "rtsp_url": rtsp_url,
                    "location": location
                })
    
    return cameras

def main():
    parser = argparse.ArgumentParser(description="CCTV Camera Setup Tool")
    parser.add_argument("--discover", action="store_true", help="Show camera discovery guide")
    parser.add_argument("--test", help="Test RTSP URL")
    parser.add_argument("--scan", help="Scan network for cameras (e.g., 192.168.1)")
    parser.add_argument("--interactive", action="store_true", help="Interactive setup")
    
    args = parser.parse_args()
    
    print("🎥 CCTV Camera Setup Tool")
    print("=" * 50)
    
    if args.discover:
        discover_camera_settings()
    elif args.test:
        test_rtsp_connection(args.test)
    elif args.scan:
        scan_network_cameras(args.scan)
    elif args.interactive:
        cameras = interactive_setup()
        
        if cameras:
            print(f"\n📋 Summary:")
            for i, camera in enumerate(cameras, 1):
                print(f"{i}. {camera['name']} ({camera['location']})")
                print(f"   RTSP: {camera['rtsp_url']}")
            
            proceed = input(f"\nAdd {len(cameras)} cameras to database? (y/N): ").strip().lower()
            if proceed == 'y':
                for camera in cameras:
                    add_camera_to_db(camera['name'], camera['rtsp_url'], camera['location'])
    else:
        print("Use --help for available options")

if __name__ == "__main__":
    main()