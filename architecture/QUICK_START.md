# Quick Start - Generate Architecture Images

## Method 1: Using Mermaid Live Editor (Easiest)

1. Go to https://mermaid.live/
2. Open any `.mmd` file from this folder
3. Copy the content
4. Paste into Mermaid Live Editor
5. Click "Download PNG" or "Download SVG"
6. Save to this folder

## Method 2: Using Mermaid CLI (Automated)

### Install Mermaid CLI
```bash
npm install -g @mermaid-js/mermaid-cli
```

### Generate All Images
```bash
cd architecture
python3 generate_diagrams.py
```

This will generate PNG files for all diagrams.

### Generate Individual Image
```bash
mmdc -i system_architecture.mmd -o system_architecture.png -b white -w 2400 -H 1800
```

## Method 3: Using VS Code

1. Install "Markdown Preview Mermaid Support" extension
2. Open `ARCHITECTURE_DIAGRAM.md` in VS Code
3. Right-click on any diagram → "Export as PNG"

## Method 4: Using GitHub

GitHub automatically renders Mermaid diagrams. Simply view `ARCHITECTURE_DIAGRAM.md` on GitHub and take screenshots.

## Diagram Files Available

- `system_architecture.mmd` - Overall system architecture
- `data_flow.mmd` - Data flow through the system
- `user_flow.mmd` - Complete user journey sequence
- `component_architecture.mmd` - Detailed component breakdown
- `score_calculation.mmd` - Score calculation flow
- `deployment_architecture.mmd` - Deployment process
- `security_flow.mmd` - Security and access flow
- `data_processing.mmd` - Data processing pipeline
- `user_interaction.mmd` - User interaction state diagram
- `dataset_relationships.mmd` - Dataset relationships

## Recommended Image Sizes

- **Width**: 2400px (for presentations)
- **Height**: 1800px (auto-adjusts)
- **Format**: PNG (for documents) or SVG (for web)

## Tips

- Use white background for documents
- Use dark background for presentations
- SVG format is scalable and better for web
- PNG format is better for documents and presentations
