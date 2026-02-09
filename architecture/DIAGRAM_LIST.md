# Architecture Diagram Files

This folder contains Mermaid diagram source files that can be converted to PNG/SVG images.

## Available Diagrams

1. **system_architecture.mmd** - Overall system architecture showing all layers
2. **data_flow.mmd** - Data flow from system tables to visualization
3. **user_flow.mmd** - Complete user journey sequence diagram
4. **component_architecture.mmd** - Detailed component breakdown
5. **score_calculation.mmd** - Score calculation flow and aggregation
6. **deployment_architecture.mmd** - Deployment process and automation
7. **security_flow.mmd** - Security and access control flow
8. **data_processing.mmd** - Data processing pipeline with 13 queries
9. **user_interaction.mmd** - User interaction state diagram
10. **dataset_relationships.mmd** - Dataset relationships and hierarchy

## How to Generate Images

### Quick Method (Online)
1. Open https://mermaid.live/
2. Copy content from any `.mmd` file
3. Paste into editor
4. Download as PNG or SVG

### Automated Method (CLI)
```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Generate all images
cd architecture
python3 generate_diagrams.py
```

### Individual Image
```bash
mmdc -i system_architecture.mmd -o system_architecture.png -b white -w 2400 -H 1800
```

## File Sizes

- **Source files (.mmd)**: ~1-2 KB each
- **Generated PNG**: ~50-200 KB each (at 2400x1800)
- **Generated SVG**: ~10-50 KB each (scalable)

## Usage

- **Presentations**: Use PNG format, 2400px width
- **Documents**: Use PNG or SVG format
- **Web**: Use SVG format for scalability
- **GitHub**: View `ARCHITECTURE_DIAGRAM.md` directly (auto-renders)
