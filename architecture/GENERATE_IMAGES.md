# Generate Architecture Diagram Images

## Quick Method (Recommended)

### Option 1: Using Mermaid Live Editor (Easiest - No Installation)

1. Go to **https://mermaid.live/**
2. Open any `.mmd` file from this folder
3. Copy the entire content
4. Paste into Mermaid Live Editor
5. Click **"Download PNG"** or **"Download SVG"**
6. Save to this `architecture/` folder
7. Repeat for all 10 diagrams

**Time**: ~2 minutes per diagram = ~20 minutes total

---

### Option 2: Using HTML Renderer (Browser-Based)

1. Open `render_diagrams.html` in your web browser
2. All diagrams will render automatically
3. For each diagram:
   - Right-click → **"Inspect"** or **"Inspect Element"**
   - Find the `<svg>` element in DevTools
   - Right-click SVG → **"Copy"** or **"Save Image As"**
   - Save as PNG
4. Or use browser screenshot tools:
   - **Mac**: Cmd+Shift+4 (select area)
   - **Windows**: Windows+Shift+S (Snipping Tool)

---

### Option 3: Using Mermaid CLI (Automated)

**Prerequisites**: Node.js and npm installed

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Generate all images
cd architecture
python3 generate_diagrams.py
```

This will automatically generate PNG files for all diagrams.

---

## Diagram Files to Generate

1. ✅ `system_architecture.png` - Overall system architecture
2. ✅ `data_flow.png` - Data flow through the system
3. ✅ `user_flow.png` - Complete user journey
4. ✅ `component_architecture.png` - Detailed components
5. ✅ `score_calculation.png` - Score calculation flow
6. ✅ `deployment_architecture.png` - Deployment process
7. ✅ `security_flow.png` - Security & access flow
8. ✅ `data_processing.png` - Data processing pipeline
9. ✅ `user_interaction.png` - User interaction states
10. ✅ `dataset_relationships.png` - Dataset relationships

---

## Image Specifications

- **Format**: PNG (recommended) or SVG
- **Width**: 2400px (for presentations)
- **Height**: Auto (maintains aspect ratio)
- **Background**: White
- **Quality**: High resolution for printing/presentations

---

## Troubleshooting

### If Mermaid Live Editor doesn't work:
- Try a different browser
- Clear browser cache
- Check internet connection

### If HTML renderer doesn't show diagrams:
- Make sure you're opening via `file://` protocol
- Or serve via a local web server: `python3 -m http.server 8000`
- Then open: `http://localhost:8000/render_diagrams.html`

### If Mermaid CLI fails:
- Ensure Node.js is installed: `node --version`
- Ensure npm is installed: `npm --version`
- Try updating: `npm update -g @mermaid-js/mermaid-cli`

---

## Next Steps

Once you have all PNG images:

1. Verify all 10 images are in the `architecture/` folder
2. Check image quality and readability
3. Images are ready to use in:
   - Documentation
   - Presentations
   - README files
   - Architecture reviews

---

**Recommended**: Use **Option 1 (Mermaid Live Editor)** - it's the fastest and most reliable method!
