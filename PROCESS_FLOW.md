# Institutional Research Pipeline: Analyst Process Flow

This document explains the Kasona Institutional Pipeline logic, simulating a human analyst's workflow for the "Loom Video" requirement.

## 1. Data Procurement (The Scrapers)
The process begins with **Real-World Scoping**. Instead of relying on static database snapshots, the AI Analyst uses:
- **EODHD**: To pull recent fundamental data and market capitalization trends.
- **Apify (YouTube)**: To find current CEO interviews and podcasts. We don't just find URLs; we pull transcripts to understand the *nuance* of the leadership's tone.
- **Apify (LinkedIn)**: To verify the current executive leadership team and their backgrounds.

## 2. Institutional Synthesis (The Brain)
We use a **Batched Synthesis Engine**. 
- **The Zero-Null Policy**: The analyst identifies missing "pillars" (Bull/Bear cases, Porter's Five Forces).
- **Context Injection**: We feed the AI the company's description and current financials. This ensures the Bull/Bear cases aren't generic—they are calculated risks based on current multiples and market position.
- **Batched Logic**: To avoid "stuttering" (rate limits), we consolidate all missing data into a single institutional-grade synthesis request.

## 3. Auditability (The Metadata Reservoir)
Every output is backed by raw data.
- **n8n-info**: This column in Supabase acts as our "Audit Log." It stores the raw JSON outputs from Apify and YouTube transcripts. If an analyst ever questions a claim in the PDF, the evidence is stored right in the database row.

## 4. Multi-Modal Artifact Generation
Finally, the "Design Team" handles the outputs:
- **PDF Engine**: Transforms the synthesis into a Kasona-branded institutional report with charts and Porter's analysis.
- **Neural Audio**: Generates a high-fidelity briefing for mobile listening.
- **Sync**: All artifacts are uploaded to Supabase storage and linked back to the main data record.

## Summary
The system operates as a **Single-Source-of-Truth** where pure data, AI reasoning, and high-fidelity artifacts are atomically synchronized.
