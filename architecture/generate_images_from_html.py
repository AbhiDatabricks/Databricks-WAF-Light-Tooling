#!/usr/bin/env python3
"""
Generate PNG images from render_diagrams.html using headless browser

This script uses Playwright to render the HTML and take screenshots of each diagram.
"""

import os
import sys
import subprocess

def check_playwright():
    """Check if Playwright is installed"""
    try:
        import playwright
        return True
    except ImportError:
        return False

def install_playwright():
    """Install Playwright"""
    print("📦 Installing Playwright...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        print(f"❌ Failed to install Playwright: {e}")
        return False

def generate_images():
    """Generate PNG images from HTML"""
    try:
        from playwright.sync_api import sync_playwright
        
        html_file = "render_diagrams.html"
        if not os.path.exists(html_file):
            print(f"❌ {html_file} not found")
            return False
        
        print("🎨 Generating images from HTML...")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Load HTML file
            file_path = os.path.abspath(html_file)
            page.goto(f"file://{file_path}")
            
            # Wait for Mermaid to render
            page.wait_for_timeout(3000)  # Wait 3 seconds for rendering
            
            # Find all diagram containers
            diagram_containers = page.query_selector_all(".diagram-container")
            
            print(f"📊 Found {len(diagram_containers)} diagrams\n")
            
            for i, container in enumerate(diagram_containers, 1):
                # Get diagram title
                title_elem = container.query_selector(".diagram-title")
                title = title_elem.inner_text() if title_elem else f"diagram_{i}"
                
                # Clean title for filename
                filename = title.lower().replace(" ", "_").replace("-", "_")
                filename = "".join(c for c in filename if c.isalnum() or c == "_")
                filename = f"{filename}.png"
                
                print(f"🖼️  Generating: {filename}...")
                
                # Take screenshot of this container
                container.screenshot(path=filename, type="png")
                
                # Check file size
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"   ✅ Created: {filename} ({size:,} bytes)")
                else:
                    print(f"   ❌ Failed to create: {filename}")
            
            browser.close()
        
        # Count generated images
        png_files = [f for f in os.listdir('.') if f.endswith('.png')]
        print(f"\n✅ Generated {len(png_files)} PNG images")
        return True
        
    except ImportError:
        print("❌ Playwright not installed")
        print("\n💡 Installing Playwright...")
        if install_playwright():
            return generate_images()  # Retry after installation
        else:
            print("\n📝 Alternative methods:")
            print("   1. Use Mermaid Live Editor: https://mermaid.live/")
            print("   2. Open render_diagrams.html in browser and take screenshots")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n📝 Alternative: Open render_diagrams.html in browser and export manually")
        return False

def main():
    print("🎨 Generate Architecture Diagram Images")
    print("=" * 70)
    
    if not check_playwright():
        print("📦 Playwright not found. Installing...")
        if not install_playwright():
            print("\n❌ Could not install Playwright automatically")
            print("   Please install manually:")
            print("   pip install playwright")
            print("   playwright install chromium")
            return
    
    success = generate_images()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ All images generated successfully!")
        print(f"📁 Location: {os.path.abspath('.')}")
    else:
        print("\n" + "=" * 70)
        print("⚠️  Could not generate images automatically")
        print("💡 Use render_diagrams.html in browser to export manually")

if __name__ == "__main__":
    main()
