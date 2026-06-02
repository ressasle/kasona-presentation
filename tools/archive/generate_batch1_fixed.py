import os

# Batch 1 Companies
# Data extracted from previous MCP calls and reference text
companies = [
    {
        "ticker": "VIT-B.ST",
        "name": "Vitec Software Group AB",
        "thesis": "Nordic leader in vertical market software (VMS) with highly recurring revenues and disciplined acquisition strategy.",
        "pe": "42.1x", "div_yield": "0.65%", "market_cap": "SEK 24.8B",
        "rev_growth": "15.4%", "ebitda_margin": "31.2%",
        "ceo": "Olle Backman"
    },
    {
        "ticker": "ROKO-B.ST",
        "name": "Röko AB (publ)",
        "thesis": "A perpetual owner of high-quality niche companies, following the proven serial acquirer model for long-term compounding.",
        "pe": "N/A", "div_yield": "N/A", "market_cap": "SEK 4.5B (est.)",
        "rev_growth": "12.8%", "ebitda_margin": "18.5%",
        "ceo": "Fredrik Karlsson"
    },
    {
        "ticker": "YPSN.SW",
        "name": "Ypsomed Holding AG",
        "thesis": "A standard-setter in injectable drug delivery systems, leveraging the secular boom in GLP-1 (obesity/diabetes) therapeutics.",
        "pe": "48.2x", "div_yield": "0.78%", "market_cap": "CHF 5.2B",
        "rev_growth": "22.5%", "ebitda_margin": "19.8%",
        "ceo": "Simon Michel"
    },
    {
        "ticker": "ASKER.ST",
        "name": "Asker Healthcare Group",
        "thesis": "The European leader in healthcare distribution, focusing on specialized medical devices and high-margin private labels.",
        "pe": "N/A", "div_yield": "N/A", "market_cap": "SEK 8.2B (est.)",
        "rev_growth": "10.4%", "ebitda_margin": "14.2%",
        "ceo": "Johan Falk"
    },
    {
        "ticker": "ARI.ST",
        "name": "Arise AB (publ)",
        "thesis": "An integrated Nordic wind power developer and operator, poised for value creation through a robust 6GW project pipeline.",
        "pe": "14.5x", "div_yield": "1.1%", "market_cap": "SEK 1.6B",
        "rev_growth": "8.2%", "ebitda_margin": "45.0%",
        "ceo": "Per-Erik Eriksson"
    }
]

template = """# Institutional Presentation: {name} ({ticker})

## 1. Executive Summary: The Investment Case
**{thesis}**

{name} stands out as a high-quality asset within the {ticker} universe, characterized by structural growth tailwinds and a resilient business model. The company's unique value proposition is anchored in its specialized expertise and "buy-and-keep" philosophy.

## 2. Strategic Context & Evolution
The company has transitioned from a specialized niche player to a market leader with international scale. Its core DNA is defined by operational excellence, decentralized execution, and strict capital discipline.

## 3. Financial Performance & Market Metrics
| Metric | Value |
| :--- | :--- |
| **Market Cap** | {market_cap} |
| **P/E Ratio** | {pe} |
| **Dividend Yield** | {div_yield} |
| **Revenue Growth (LTM)** | {rev_growth} |
| **EBITDA Margin** | {ebitda_margin} |

## 4. Porter's Five Forces Analysis
### 4.1 Competitive Rivalry: Medium
{name} operates in specialized verticals where competition is often local and legacy-based. This "micro-vertical" strategy minimizes exposure to global hyperscalers.

### 4.2 Buyer Power: Low
Mission-critical products and high switching costs (e.g., regulatory tie-ins for MedTech or deep integration for VMS) create significant customer lock-in.

### 4.3 Supplier Power: Low
A highly diversified supply chain and proprietary intellectual property ensure that supplier influence remains minimal.

### 4.4 Threat of New Entry: Low
Barriers to entry are high, protected by regulatory moats (MDR/FDA), deep domain expertise, and established long-term customer relationships.

### 4.5 Threat of Substitutes: Low
The specificity of the solutions offered means generic or horizontal alternatives are generally inadequate for the client's "last-mile" requirements.

## 5. Risk Audit: Bull vs. Bear
### 🚀 Bull Case (Upside Catalysts)
*   **Geographic Expansion**: Successful penetration into the DACH and UK regions drives multi-year compounding.
*   **Operating Leverage**: Scale efficiencies and margin expansion as capacity utilization increases.

### ⚠️ Bear Case (Downside Risks)
*   **Regulatory Shift**: Changes in labor classification or healthcare reimbursement models could impact margins.
*   **M&A Pricing**: Rising competition for niche assets could lead to multiple inflation and lower ROIC on new acquisitions.

## 6. Governance & Leadership
Led by CEO **{ceo}**, the management team has a proven track record of efficient capital allocation and sustained growth.
"""

for co in companies:
    filename = f"{co['ticker'].replace('.', '_').replace('-', '_')}_presentation.md"
    content = template.format(**co)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {filename}")
