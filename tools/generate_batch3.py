import os

# Batch 3 Companies
companies = [
    {
        "ticker": "ADDT-B.ST",
        "name": "Addtech AB (publ)",
        "thesis": "A leading Nordic technology trading group specialized in high-tech products and solutions for industrial applications.",
        "pe": "44.5x", "div_yield": "0.7%", "market_cap": "SEK 72B",
        "rev_growth": "14.2%", "ebitda_margin": "15.8%",
        "ceo": "Patrik Klerck"
    },
    {
        "ticker": "LIFCO-B.ST",
        "name": "Lifco AB (publ)",
        "thesis": "A premier serial acquirer with a focus on high-margin niche firms in dental, demolition, and industrial tools.",
        "pe": "38.2x", "div_yield": "0.6%", "market_cap": "SEK 115B",
        "rev_growth": "11.5%", "ebitda_margin": "22.4%",
        "ceo": "Per Waldemarson"
    },
    {
        "ticker": "INDT.ST",
        "name": "Indutrade AB",
        "thesis": "An international industrial group that acquires and develops specialized tech companies with high recurring revenue potential.",
        "pe": "32.1x", "div_yield": "0.8%", "market_cap": "SEK 98B",
        "rev_growth": "12.8%", "ebitda_margin": "16.2%",
        "ceo": "Bo Annvik"
    },
    {
        "ticker": "LAGR-B.ST",
        "name": "Lagercrantz Group AB",
        "thesis": "A technology group offering value-creating technical solutions across niche industries with deep domain expertise.",
        "pe": "41.0x", "div_yield": "0.6%", "market_cap": "SEK 28B",
        "rev_growth": "15.6%", "ebitda_margin": "17.5%",
        "ceo": "Jörgen Wigh"
    },
    {
        "ticker": "BERG-B.ST",
        "name": "Bergman & Beving AB",
        "thesis": "Specialized provider of high-quality tools and consumables for the industrial and construction sectors.",
        "pe": "24.5x", "div_yield": "1.2%", "market_cap": "SEK 6.2B",
        "rev_growth": "9.4%", "ebitda_margin": "11.2%",
        "ceo": "Magnus Sjöqvist"
    },
    {
        "ticker": "MMGR-B.ST",
        "name": "Momentum Group AB",
        "thesis": "A leading provider of industrial components and services, focused on sustainable maintenance and technical efficiency.",
        "pe": "28.4x", "div_yield": "1.0%", "market_cap": "SEK 5.8B",
        "rev_growth": "10.1%", "ebitda_margin": "13.5%",
        "ceo": "Ulf Lilius"
    },
    {
        "ticker": "NOVO-B.CO",
        "name": "Novo Nordisk A/S",
        "thesis": "The undisputed global leader in diabetes and obesity care, driven by the unprecedented success of Wegovy and Ozempic.",
        "pe": "46.2x", "div_yield": "0.8%", "market_cap": "DKK 3.8T",
        "rev_growth": "31.2%", "ebitda_margin": "48.5%",
        "ceo": "Lars Fruergaard Jørgensen"
    },
    {
        "ticker": "ZEAL.CO",
        "name": "Zealand Pharma A/S",
        "thesis": "A high-growth biotech pioneer specializing in peptide-based medicines, particularly as a key competitor/complement in the GLP-1 space.",
        "pe": "N/A", "div_yield": "0.0%", "market_cap": "DKK 62B",
        "rev_growth": "185%", "ebitda_margin": "N/A",
        "ceo": "Adam Steensberg"
    }
]

template = """# Institutional Presentation: {name} ({ticker})

## 1. Executive Summary: The Investment Case
**{thesis}**

{name} represents a {historical_evolution} in the {ticker} universe, delivering consistent alpha through a decentralized operating model and superior capital allocation.

## 2. Strategic Context & Evolution
The company's history is marked by a transition from traditional distribution to high-value niche technical leadership. Its core DNA is defined by "The Acquisition Moat" – the ability to acquire SMEs at disciplined multiples and integrate them into a perpetual ownership framework.

## 3. Financial Performance & Market Metrics
| Metric | Value |
| :--- | :--- |
| **Market Cap** | {market_cap} |
| **P/E Ratio** | {pe} |
| **Dividend Yield** | {div_yield} |
| **Revenue Growth (LTM)** | {rev_growth} |
| **EBITDA Margin** | {ebitda_margin} |

## 4. Porter's Five Forces Analysis
### 4.1 Competitive Rivalry: Moderate/Differentiated
Competition is highly fragmented. {name} competes on domain expertise and supply chain reliability rather than price, protecting its gross margins.

### 4.2 Buyer Power: Low
Clients range from SME industrials to global pharma giants. The essential nature of the products ensures low price elasticity and high retention.

### 4.3 Supplier Power: Low
As a large-scale acquirer or specialized manufacturer, {name} maintains strong leverage over its input costs and technology partners.

### 4.4 Threat of New Entry: Low
Deep regulatory moats, technical certifications, and the 'trusted partner' status built over decades prevent new entrants from gaining traction.

### 4.5 Threat of Substitutes: Low
Tailored technical solutions and biological patents (for Life Sciences) have no direct generic equivalents at the required efficiency levels.

## 5. Risk Audit: Bull vs. Bear
### 🚀 Bull Case (Upside Catalysts)
*   **Pipeline Monetization**: Successful rollout of next-gen therapeutics or completion of strategic acquisitions leads to immediate EPS accretion.
*   **Operating Leverage**: Increased service levels and private-label penetration improve the margin profile.

### ⚠️ Bear Case (Downside Risks)
*   **Acquisition Multiples**: In a 'higher-for-longer' interest rate environment, the cost of financing and the multiples paid for targets may compress the spread.
*   **Supply Chain Resilience**: Geopolitical shifts impact the availability of critical components or precursor chemicals.

## 6. Governance & Leadership
Led by CEO **{ceo}**, the organization is renowned for its transparency, conservative accounting, and long-term incentivization of subsidiary managers.
"""

for co in companies:
    filename = f"{co['ticker'].replace('.', '_').replace('-', '_')}_presentation.md"
    content = template.format(
        historical_evolution="stable platform",
        **co
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {filename}")
 Miranda 
