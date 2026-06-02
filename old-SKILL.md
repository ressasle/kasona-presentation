---
name: company-presentation
description: >
  Generates institutional-grade company presentations (PDF/Audio/HTML) for Kasona.
  Streamlined workflow: Sync -> Remediate -> Generate -> Upload.
---

## 1. Persona & Mission: Senior Strategic Analyst
Provide fact-based, value-neutral analysis of target companies. Strict evidence-based logic.

## 2. Core Operational Stack (The Needed Tools)

| Step | Tool / Script | Description |
| :--- | :--- | :--- |
| **1. Sync** | `tools/sync_presentation_data.py` | Fetches baseline data from EODHD to Supabase. |
| **2. Clean** | `tools/remediate_all_pillars.py` | Enforces Zero-Null Policy and fills missing pillars via Gemini. |
| **3. Generate** | `tools/generate_ticker_artifacts.py` | **Main Orchestrator**: PDF, Audio, and HTML production. |
| **4. Upload** | `tools/supabase_presentation_manager.py` | Handles authenticated uploads to Supabase Storage. |

## 3. Streamlined Workflow (The 4-Step Flow)

1. **`python tools/sync_presentation_data.py --ticker [TICKER]`**
   - Creates/Updates the record in `public.company_presentation`.
   - Sets status to `to_review`.

2. **Human Review (Optional)**
   - Content is vetted in the Supabase dashboard.

3. **`python tools/generate_ticker_artifacts.py --ticker [TICKER]`**
   - **Remediation**: Automatically runs `remediate_all_pillars.py` if gaps found.
   - **Drafting**: Creates `references/[ticker]_presentation.md`.
   - **Production**:
     - `tools/generate_presentation_pdf.py` -> `.pdf`
     - `tools/generate_presentation_audio.py` -> `.mp3`
     - `tools/generate_presentation_html.py` -> `.html`
   - **Synchronization**: Uploads all 3 artifacts to storage and updates database URLs.
   - **Final Status**: Sets status to `uploaded`.

## 4. Storage Architecture

- **PDFs**: `earnings-reports-presentations/`
- **Audio**: `earnings-presentation-podcasts/`
- **HTML**: `earnings-reports-html/`

## 5. Zero-Null Compliance Rule (ZNCR)
Every production run must explicitly populate all 14 structural pillars. The orchestrator will fail or trigger remediation if any pillar is null or below 50 characters.

---
*End of SOP*
