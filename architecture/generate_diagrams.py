#!/usr/bin/env python3
"""
Generate PNG images from Mermaid diagrams in ARCHITECTURE_DIAGRAM.md

Requirements:
    npm install -g @mermaid-js/mermaid-cli

Usage:
    python3 generate_diagrams.py
"""

import os
import re
import subprocess
import sys

ARCHITECTURE_DOC = "../ARCHITECTURE_DIAGRAM.md"
OUTPUT_DIR = "."

# Diagram names and their section headers
DIAGRAMS = [
    ("system_architecture", "System Architecture Overview"),
    ("data_flow", "Data Flow Architecture"),
    ("user_flow", "User Flow - Complete Journey"),
    ("component_architecture", "Detailed Component Architecture"),
    ("score_calculation", "Score Calculation Flow"),
    ("deployment_architecture", "Deployment Architecture"),
    ("security_flow", "Security & Access Flow"),
    ("data_processing", "Data Processing Pipeline"),
    ("user_interaction", "User Interaction Flow"),
    ("dataset_relationships", "Dataset Relationship Architecture"),
]

def extract_mermaid_code(content, section_name):
    """Extract Mermaid code block for a given section"""
    # Find the section
    pattern = rf"## .*{re.escape(section_name)}.*?\n```mermaid\n(.*?)```"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return None

def check_mermaid_cli():
    """Check if mermaid-cli is installed"""
    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def generate_image(mermaid_code, output_file):
    """Generate PNG image from Mermaid code using mmdc"""
    # Create temporary mermaid file
    temp_file = f"{output_file}.mmd"
    
    try:
        with open(temp_file, 'w') as f:
            f.write(mermaid_code)
        
        # Run mmdc
        result = subprocess.run(
            [
                "mmdc",
                "-i", temp_file,
                "-o", f"{output_file}.png",
                "-b", "white",
                "-w", "2400",
                "-H", "1800"
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Generated: {output_file}.png")
            return True
        else:
            print(f"❌ Error generating {output_file}.png:")
            print(result.stderr)
            return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    print("🎨 Generating Architecture Diagrams")
    print("=" * 70)
    
    # Check if mermaid-cli is installed
    if not check_mermaid_cli():
        print("❌ Mermaid CLI (mmdc) not found!")
        print("\nPlease install it first:")
        print("  npm install -g @mermaid-js/mermaid-cli")
        print("\nOr use the online tool:")
        print("  https://mermaid.live/")
        sys.exit(1)
    
    # Read architecture document
    doc_path = os.path.join(os.path.dirname(__file__), ARCHITECTURE_DOC)
    if not os.path.exists(doc_path):
        print(f"❌ Architecture document not found: {doc_path}")
        sys.exit(1)
    
    with open(doc_path, 'r') as f:
        content = f.read()
    
    # Generate images for each diagram
    success_count = 0
    for diagram_name, section_name in DIAGRAMS:
        print(f"\n📊 Processing: {diagram_name}...")
        
        mermaid_code = extract_mermaid_code(content, section_name)
        
        if not mermaid_code:
            print(f"⚠️  Could not find diagram for: {section_name}")
            continue
        
        output_file = os.path.join(OUTPUT_DIR, diagram_name)
        
        if generate_image(mermaid_code, output_file):
            success_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Generated {success_count}/{len(DIAGRAMS)} diagrams")
    print(f"📁 Output directory: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    main()
