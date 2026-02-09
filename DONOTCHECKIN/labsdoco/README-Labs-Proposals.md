# Labs Proposals – Templates and WAF-AUTO

This folder contains **Labs proposal templates** and **filled content** for the **WAF-AUTO (WAF Light Tooling)** project.

## Files

| File | Purpose |
|------|--------|
| **WAF-AUTO- Labs Proposal_ Project Template.docx** | Official Labs proposal template (blank). Use this as the document you submit. |
| **Labs Proposal_ Ontos.docx** | **Reference template** – filled example (Ontos project). Use for section order, tone, and level of detail. |
| **Labs Proposal_ Zerobus - file mode.pdf** | **Reference template** – another filled Labs proposal (Zerobus). Use for structure and checklist style. |
| **WAF-AUTO-Labs-Proposal-Filled.md** | **Filled content for WAF-AUTO.** Copy from here into the Word template. |

## How to fill the WAF-AUTO Labs proposal

1. **Open** `WAF-AUTO- Labs Proposal_ Project Template.docx`.
2. **Use** `Labs Proposal_ Ontos.docx` (and optionally Zerobus PDF) to see how each section should be filled (length, style, checkboxes).
3. **Copy** each section from `WAF-AUTO-Labs-Proposal-Filled.md` into the matching section of the template:
   - Title and one-sentence description  
   - Owners, Status, Product (team), Artifact, Repository, Language, Target release, Go link  
   - Part 1: Customer evidence, Markitecture, Graduation strategy, Project kickoff, Administrative actions  
   - Part 2: Design sketch, Alternatives, Uncertainties, Project tracking  
   - Part 3: Launch checklist (API Clients, Python projects, Administration, Enablement, CI, Security & Legal, Longevity, Marketing)  
   - Review status table  
4. **Replace placeholders** in the filled content (e.g. `@YOURNAME`, `@PMNAME`, `YYYY-MM-DD`, customer names, LPP-XXX, SDR-XXX) with real values before submission.
5. **Add** a Markitecture diagram (e.g. from [Mermaid](https://mermaid.live/) or [Excalidraw](https://excalidraw.com/)) as in the template instructions.

## Template structure (from Ontos / Zerobus)

- **Header:** Project name, one-sentence description, Owners, Status, Product, Artifact, Repo, Language, Target release, Go link.  
- **Part 1 – Request for comments:** Customer evidence (≥10 customers, GTM), Markitecture, Graduation strategy, Project kickoff, Administrative actions.  
- **Part 2 – Design sketch:** Problem/CUJ, design summary, diagram; optional Alternatives and Uncertainties; Project tracking.  
- **Part 3 – Launch checklist:** API Clients, Notebook Libraries, Java/Scala, Python, Administration, Enablement, CI, Security & Legal, Longevity, Marketing.  
- **Review status:** Table with Labs, PM, Legal, Security reviewers and LGTM/dates/ticket numbers.

## WAF-AUTO details in the codebase

- **README.md** – Problem, solution, end users.  
- **DEPLOYMENT_SUMMARY.md** – What’s deployed (dashboard + app), URLs, known issues.  
- **WAF_DASHBOARD_GUIDE.md**, **WAF_CHARTS_SUMMARY.md** – Metrics and WAF identifiers.  
- **streamlit-waf-automation/app.py**, **install.ipynb** – App and dashboard deployment.  
- **DONOTCHECKIN/Well-Architected Framework (WAF) - 22042025.xlsx** – Source WAF structure.

Use the Ontos and Zerobus proposals as the **templates** for format and structure; use **WAF-AUTO-Labs-Proposal-Filled.md** as the **content** to paste into **WAF-AUTO- Labs Proposal_ Project Template.docx**.
