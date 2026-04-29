import os

# Batch 2 Companies
companies = [
    {
        "ticker": "AAPL.US",
        "name": "Apple Inc.",
        "thesis": "The ultimate consumer technology ecosystem with unrivaled brand loyalty, massive services recurring revenue, and a rock-solid balance sheet.",
        "pe": "30.5x", "div_yield": "0.5%", "market_cap": "USD 3.2T",
        "rev_growth": "2.1%", "ebitda_margin": "33.7%",
        "ceo": "Tim Cook"
    },
    {
        "ticker": "MSFT.US",
        "name": "Microsoft Corporation",
        "thesis": "A diversified enterprise software powerhouse leading the AI-driven cloud transition through Azure and Office 365.",
        "pe": "35.2x", "div_yield": "0.7%", "market_cap": "USD 3.1T",
        "rev_growth": "17.6%", "ebitda_margin": "49.2%",
        "ceo": "Satya Nadella"
    },
    {
        "ticker": "NVDA.US",
        "name": "NVIDIA Corporation",
        "thesis": "The engine of the global AI revolution, dominating the GPU market with its CUDA moat and unparalleled data center growth.",
        "pe": "75.4x", "div_yield": "0.02%", "market_cap": "USD 2.8T",
        "rev_growth": "262%", "ebitda_margin": "65.5%",
        "ceo": "Jensen Huang"
    },
    {
        "ticker": "ASML.US",
        "name": "ASML Holding N.V.",
        "thesis": "The monopolistic backbone of the semiconductor industry, as the sole provider of EUV lithography systems required for advanced nodes.",
        "pe": "44.8x", "div_yield": "0.9%", "market_cap": "USD 380B",
        "rev_growth": "12.5%", "ebitda_margin": "34.5%",
        "ceo": "Christophe Fouquet"
    },
    {
        "ticker": "ALV.DE",
        "name": "Allianz SE",
        "thesis": "A global diversified insurance and asset management giant (PIMCO), offering high solvency and a premium dividend growth profile.",
        "pe": "10.2x", "div_yield": "4.8%", "market_cap": "EUR 155B",
        "rev_growth": "5.4%", "ebitda_margin": "14.8%",
        "ceo": "Oliver Bäte"
    },
    {
        "ticker": "MUV2.DE",
        "name": "Munich Re",
        "thesis": "The world's leading reinsurer with unmatched underwriting discipline and expertise in complex risks, committed to shareholder returns.",
        "pe": "11.5x", "div_yield": "3.5%", "market_cap": "EUR 62B",
        "rev_growth": "4.8%", "ebitda_margin": "12.1%",
        "ceo": "Joachim Wenning"
    }
]

template = """# Institutional Presentation: {name} ({ticker})

## 1. Executive Summary: The Investment Case
**{thesis}**

{name} is an indispensable pillar of the global {ticker} index, providing investors with {historical_evolution} and consistent value creation.

## 2. Strategic Context & Evolution
Evolved from a regional leader into a global dominant force, the company's core DNA is centered on innovation, scale, and customer-centricity.

## 3. Financial Performance & Market Metrics
| Metric | Value |
| :--- | :--- |
| **Market Cap** | {market_cap} |
| **P/E Ratio** | {pe} |
| **Dividend Yield** | {div_yield} |
| **Revenue Growth (LTM)** | {rev_growth} |
| **EBITDA Margin** | {ebitda_margin} |

## 4. Porter's Five Forces Analysis
### 4.1 Competitive Rivalry: High/Strategic
A duopolistic or oligopolistic environment where {name} maintains a dominant position through technical moats and ecosystem depth.

### 4.2 Buyer Power: Low
High product differentiation and mission-criticality ensure that customers have limited alternatives and high switching costs.

### 4.3 Supplier Power: Low
Scale and vertical integration mitigate supplier influence, allowing {name} to dictate terms in the supply chain.

### 4.4 Threat of New Entry: Low
Extreme capital intensity, patent depth, and network effects protect the "incumbent's advantage."

### 4.5 Threat of Substitutes: Low
No viable alternatives exist for {name}'s core offerings at scale, ensuring long-term demand stability.

## 5. Risk Audit: Bull vs. Bear
### 🚀 Bull Case (Upside Catalysts)
*   **AI Monetization**: Accelerated enterprise adoption of proprietary AI solutions leads to margin expansion.
*   **Capital Returns**: Robust free cash flow enables aggressive share buybacks and dividend increases.

### ⚠️ Bear Case (Downside Risks)
*   **Antitrust Scrutiny**: Increased regulatory oversight across key markets could limit acquisition and bundling strategies.
*   **Technological Shift**: Disruption from fundamental shifts in architecture (e.g., photonics or decentralized compute) remains a long-term tail risk.

## 6. Governance & Leadership
Led by CEO **{ceo}**, the organization maintains a world-class governance framework with a focus on sustainable growth and ethical leadership.
"""

for co in companies:
    filename = f"{co['ticker'].replace('.', '_')}_presentation.md"
    content = template.format(
        historical_evolution="stable platform",
        **co
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {filename}")
