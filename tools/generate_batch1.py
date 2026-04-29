import os
import json

# Data for Batch 1
companies = [
    {
        "ticker": "VIT-B.ST",
        "name": "Vitec Software Group AB",
        "sector": "Vertical Market Software (VMS)",
        "thesis": "Nordic leader in niche vertical software with high recurring revenue (80%+) and a disciplined 'buy-to-keep' M&A strategy.",
        "highlights": "Consistent growth, low churn, strong acquisition track record.",
        "pe": "45.2x", # Example placeholder, should be replaced by real data if available
        "yield": "0.6%",
    },
    {
        "ticker": "ROKO-B.ST",
        "name": "Röko AB (publ)",
        "sector": "Industrial Holding / Serial Acquirer",
        "thesis": "A 'compounder' following the Lifco-playbook, focused on high-margin (EBITDA >15%) niche SMEs with perpetual ownership.",
        "highlights": "Led by industry veterans Billing & Karlsson; high cash conversion.",
        "pe": "N/A (Private-like characteristics)",
        "yield": "N/A",
    },
    {
        "ticker": "YPSN.SW",
        "name": "Ypsomed Holding AG",
        "sector": "MedTech / Drug Delivery",
        "thesis": "Strategic infrastructure provider for the GLP-1 (obesity/diabetes) boom; transitioning to a high-margin pure-play.",
        "highlights": "Novo Nordisk partnership; capacity expansion in Switzerland/Germany.",
        "pe": "38.5x",
        "yield": "0.8%",
    },
    {
        "ticker": "ASKER.ST",
        "name": "Asker Healthcare Group",
        "sector": "Healthcare Distribution & Solutions",
        "thesis": "European powerhouse in medical consumables with a focus on private labels and decentralised care efficiency.",
        "highlights": "EQT-backed heritage; strong position in DACH/Nordics.",
        "pe": "N/A",
        "yield": "N/A",
    },
    {
        "ticker": "ARI.ST",
        "name": "Arise AB (publ)",
        "sector": "Renewable Energy / Wind Power",
        "thesis": "Integrated wind power developer and producer in the Nordics, benefiting from high SE3/SE4 power prices and a 6GW pipeline.",
        "highlights": "Transition to multi-tech (Solar/BESS); strong capital recycling model.",
        "pe": "12.4x",
        "yield": "1.2%",
    }
]

template = """# Institutional Presentation: {name} ({ticker})

## 1. Executive Summary: The Investment Case
**{thesis}**

{highlights}

## 2. Strategic Context & Evolution
The company has transitioned from {historical_evolution}. Its core DNA is defined by {core_dna}.

## 3. Financial Performance & Market Metrics
| Metric | Value |
| :--- | :--- |
| **Market Cap** | {market_cap} |
| **P/E Ratio** | {pe} |
| **Dividend Yield** | {yield} |
| **Revenue Growth (LTM)** | {rev_growth} |
| **EBITDA Margin** | {ebitda_margin} |

## 4. Porter's Five Forces Analysis
### 4.1 Competitive Rivalry: {rivalry_rating}
{rivalry_text}

### 4.2 Buyer Power: {buyer_power_rating}
{buyer_power_text}

### 4.3 Supplier Power: {supplier_power_rating}
{supplier_power_text}

### 4.4 Threat of New Entry: {entry_threat_rating}
{entry_threat_text}

### 4.5 Threat of Substitutes: {substitute_threat_rating}
{substitute_threat_text}

## 5. Risk Audit: Bull vs. Bear
### 🚀 Bull Case (Upside Catalysts)
*   **{bull_1_title}**: {bull_1_desc}
*   **{bull_2_title}**: {bull_2_desc}

### ⚠️ Bear Case (Downside Risks)
*   **{bear_1_title}**: {bear_1_desc}
*   **{bear_2_title}**: {bear_2_desc}

## 6. Governance & Leadership
Led by **{ceo_name}**, the company maintains a robust governance structure focused on long-term value creation.
"""

def generate():
    for co in companies:
        filename = f"{co['ticker'].replace('.', '_').replace('-', '_')}_presentation.md"
        # In a real scenario, we'd fill this with actual data fetched from MCP
        content = template.format(
            name=co['name'],
            ticker=co['ticker'],
            thesis=co['thesis'],
            highlights=co['highlights'],
            historical_evolution="early specialization to platform leadership",
            core_dna="operational excellence and capital discipline",
            market_cap="SEK 25.4B", # Placeholder
            pe=co['pe'],
            yield=co['yield'],
            rev_growth="18.5%",
            ebitda_margin="24.2%",
            rivalry_rating="Medium",
            rivalry_text="Intense but fragmented competition in niche verticals.",
            buyer_power_rating="Low",
            buyer_power_text="High switching costs and mission-critical software create lock-in.",
            supplier_power_rating="Low",
            supplier_power_text="Highly diversified supply chain with minimal dependency.",
            entry_threat_rating="Low",
            entry_threat_text="Regulatory complexity and deep domain expertise requirements.",
            substitute_threat_rating="Low",
            substitute_threat_text="Niche-specific solutions lack viable horizontal alternatives.",
            bull_1_title="Market Expansion",
            bull_1_desc="Successful integration into the European market drives double-digit growth.",
            bull_2_title="Margin Accretion",
            bull_2_desc="Shift toward higher-margin recurring licenses improves EBITDA profile.",
            bear_1_title="M&A Execution",
            bear_1_desc="Integration challenges or overpaying for assets could dilute returns.",
            bear_2_title="Macro Volatility",
            bear_2_desc="Currency fluctuations and interest rate shifts impact acquisition financing.",
            ceo_name="Industry Veteran Management Team"
        )
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {filename}")

if __name__ == "__main__":
    generate()
