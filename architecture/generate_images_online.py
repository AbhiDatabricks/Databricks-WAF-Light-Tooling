#!/usr/bin/env python3
"""
Generate PNG images from Mermaid diagrams using online API

This script uses the Kroki.io API to convert Mermaid diagrams to PNG images.
No local installation required!
"""

import os
import requests
import base64
import json
from urllib.parse import quote

KROKI_API = "https://kroki.io/mermaid/png"

def generate_image_online(mermaid_code, output_file):
    """Generate PNG image using Kroki.io API"""
    try:
        # Encode the mermaid code
        encoded = base64.urlsafe_b64encode(
            mermaid_code.encode('utf-8')
        ).decode('utf-8').rstrip('=')
        
        # Make API request
        url = f"{KROKI_API}/{encoded}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # Save PNG file
            with open(output_file, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"   ⚠️  API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

def main():
    print("🎨 Generating Architecture Diagram Images")
    print("=" * 70)
    print("Using Kroki.io online API (no installation required)")
    print("=" * 70)
    
    # Get all .mmd files
    mmd_files = [f for f in os.listdir('.') if f.endswith('.mmd')]
    
    if not mmd_files:
        print("❌ No .mmd files found in current directory")
        return
    
    print(f"\n📊 Found {len(mmd_files)} Mermaid diagram files\n")
    
    success_count = 0
    for mmd_file in sorted(mmd_files):
        png_file = mmd_file.replace('.mmd', '.png')
        print(f"🖼️  Generating: {png_file}...")
        
        # Read mermaid code
        with open(mmd_file, 'r') as f:
            mermaid_code = f.read()
        
        # Generate image
        if generate_image_online(mermaid_code, png_file):
            # Check file size
            size = os.path.getsize(png_file)
            print(f"   ✅ Created: {png_file} ({size:,} bytes)")
            success_count += 1
        else:
            print(f"   ❌ Failed to generate: {png_file}")
    
    print("\n" + "=" * 70)
    print(f"✅ Generated {success_count}/{len(mmd_files)} PNG images")
    print(f"📁 Location: {os.path.abspath('.')}")
    
    if success_count < len(mmd_files):
        print("\n💡 If some images failed, try:")
        print("   1. Check internet connection")
        print("   2. Use Mermaid Live Editor: https://mermaid.live/")
        print("   3. Install Mermaid CLI: npm install -g @mermaid-js/mermaid-cli")

if __name__ == "__main__":
    main()
