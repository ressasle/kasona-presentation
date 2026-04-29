# Advisory: Compute & API Rate Limits

**Subject:** Gemini API Quota Hardening

## Current Bottleneck
The institutional pipeline is currently operating under a strict **~1 RPM (Request Per Minute)** quota on the Gemini 2.0/Pro models. This is likely due to account-level compute tiers on the Anti-Gravity/Google Cloud side.

## Implemented Mitigation
1. **Batched Synthesis**: We have reduced API pressure by 80% by consolidating 7-14 individual data pillars into a single batched request.
2. **Exponential Backoff**: The scripts now include a 45s-180s cooldown between retries to avoid "Blacklisting."
3. **Model Rotation**: We successfully rotate between `gemini-2.0-flash`, `gemini-flash-latest`, and `gemini-pro-latest` to find available windows.

## Recommendation
To achieve "Enterprise Velocity" for the full 99-SA portfolio, we recommend:
- **Tier Upgrade**: Whitelisting the current API key for higher TPM (Tokens Per Minute) and RPM.
- **Credit Assignment**: Ensuring the billing account has sufficient credits to move from "Free Trial" to "Pay-As-You-Go" tier.

*Contact Anti-Gravity support with this diagnosis to request a quota increase.*
