#!/usr/bin/env python3
"""Test Google Maps API key injection"""
import os

# Set the API key
os.environ['GOOGLE_MAPS_API_KEY'] = "AIzaSyDyFXHN3VqQ9kWvj9ihcLjkpemf1FBc3uo"

print("Testing Google Maps API key injection...")
print(f"API Key set: {os.getenv('GOOGLE_MAPS_API_KEY')[:10]}...")

# Read the template
with open("templates/farmer_registration.html", "r") as f:
    content = f.read()

# Check if placeholder exists
if "YOUR_GOOGLE_MAPS_API_KEY" in content:
    print("✅ Template has placeholder 'YOUR_GOOGLE_MAPS_API_KEY'")
    
    # Replace it
    google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY', '')
    if google_maps_api_key and google_maps_api_key != 'YOUR_GOOGLE_MAPS_API_KEY':
        content = content.replace('YOUR_GOOGLE_MAPS_API_KEY', google_maps_api_key)
        
        # Check if replacement worked
        if google_maps_api_key in content:
            print("✅ API key successfully injected into template")
            print(f"   Found at position: {content.find(google_maps_api_key)}")
        else:
            print("❌ API key replacement failed")
    else:
        print("❌ No valid API key found in environment")
else:
    print("❌ Template doesn't have 'YOUR_GOOGLE_MAPS_API_KEY' placeholder")

# Check the script URL
import re
script_match = re.search(r'src="https://maps.googleapis.com/maps/api/js\?key=([^&"]+)', content)
if script_match:
    print(f"\nGoogle Maps script URL uses key: {script_match.group(1)[:10]}...")