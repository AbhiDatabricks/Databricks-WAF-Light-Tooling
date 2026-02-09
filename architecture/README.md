# Architecture Diagrams

This folder contains visual architecture diagrams for the WAF Assessment Tool.

## Generating Images

The diagrams are defined in `ARCHITECTURE_DIAGRAM.md` using Mermaid syntax. To generate PNG/SVG images:

### Option 1: Using Mermaid CLI (Recommended)

1. Install Mermaid CLI:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. Run the generation script:
   ```bash
   cd architecture
   python3 generate_diagrams.py
   ```

### Option 2: Using Online Tools

1. Copy Mermaid code from `ARCHITECTURE_DIAGRAM.md`
2. Paste into [Mermaid Live Editor](https://mermaid.live/)
3. Export as PNG or SVG
4. Save to this folder

### Option 3: Using GitHub

GitHub automatically renders Mermaid diagrams in markdown files. View `../ARCHITECTURE_DIAGRAM.md` directly on GitHub.

## Diagram Files

Once generated, you'll have:
- `system_architecture.png` - Overall system architecture
- `data_flow.png` - Data flow through the system
- `user_flow.png` - Complete user journey
- `component_architecture.png` - Detailed component breakdown
- `score_calculation.png` - Score calculation flow
- `deployment_architecture.png` - Deployment process
- `security_flow.png` - Security and access flow
- `data_processing.png` - Data processing pipeline
- `user_interaction.png` - User interaction states
- `dataset_relationships.png` - Dataset relationships

## Tools

- **Mermaid Live Editor**: https://mermaid.live/
- **Mermaid CLI**: https://github.com/mermaid-js/mermaid-cli
- **VS Code Extension**: Mermaid Preview
