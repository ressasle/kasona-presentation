---
description: Manual Video Sourcing Process for Institutional Research
---

# Institutional Video Sourcing Sub-Skill

This sub-skill defines the high-fidelity procurement process for video artifacts (interviews, podcasts, earnings calls) to ensure institutional-grade depth in the Kasona pipeline.

## 1. Objectives
- Identify the most recent "Deep Dive" interviews with the CEO/CFO.
- Procure full-length podcasts from industry-standard channels (e.g., Bloomberg, Acquired, Lex Fridman).
- Extract mission-critical transcripts for L4 synthesis.

## 2. Searching Strategy
When searching for video content, use the following prioritized search terms:
1. `[Company Name] CEO Interview [Year]`
2. `[Company Name] CFO Interview [Year]`
3. `[Company Name] Investor Day [Year]`
4. `[Company Name] Podcast Deep Dive`

## 3. Mandatory Metadata (Zero-Null Policy)
Every sourced video MUST be stored with:
- **`url`**: Direct YouTube/Vimeo link.
- **`title`**: Official video title.
- **`source`**: Channel name (e.g., "Wall Street Journal").
- **`transcript_status`**: (Available | Missing).

## 4. Integration with Supabase
All sourced video objects must be stored in the `youtube_ceo_interview` or `youtube_podcast` columns in a JSONB format including:
```json
{
  "url": "...",
  "title": "...",
  "summary": "...",
  "transcript_snippets": "..."
}
```

## 5. Quality Control
- **Recency**: Prioritize videos within the last 12-18 months.
- **Expertise**: Favor institutional channels over retail/influencer content.
- **Audio Quality**: Ensure clear audio for TTS/Neural analysis.
