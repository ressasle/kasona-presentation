import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

def update_ticker_pillars(ticker, pillars):
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return
    supabase = create_client(url, key)
    try:
        supabase.table("company_presentation").update(pillars).eq("ticker_eod", ticker).execute()
        print(f"[SUCCESS] Updated {ticker}")
    except Exception as e:
        print(f"[ERROR] Failed to update {ticker}: {e}")

# Data for the Big 5
data = {
    "ASML.US": {
        "bull-case": "1. EUV Monopoly: ASML is the sole provider of Extreme Ultraviolet (EUV) lithography systems, making it the indispensable gatekeeper of the global semiconductor roadmap. \n2. Massive Backlog: The company maintains a multi-billion dollar order backlog, providing clear visibility into mid-term revenue growth. \n3. Secular AI Tailwinds: As AI chips require increasingly dense logic, ASML's High-NA EUV roadmap ensures long-term technological leadership.",
        "bear-case": "1. Geopolitical Risk: Export restrictions to China create significant revenue headwinds and operational uncertainty. \n2. Single-Source Dependency: ASML relies on a highly specialized supply chain (e.g., Zeiss); any disruption there halts their multi-million dollar system production. \n3. Cyclical Timing: High valuation makes the stock sensitive to minor deviations in the semiconductor capex cycle.",
        "rivalry": "Low: ASML has a virtual monopoly in the high-end lithography market (EUV).",
        "supplier-power": "High: Reliance on hyper-specialized suppliers like Zeiss creates concentrated risk.",
        "buyer-power": "Low: Major chipmakers (TSMC, Intel, Samsung) have no alternative for leading-edge EUV systems.",
        "threat-of-entry": "Minimal: The capital and R&D requirements are astronomical, with moats built over 30 years.",
        "substitutes": "None: No viable alternative technologies exist for 2nm/3nm mass production."
    },
    "NVDA.US": {
        "bull-case": "1. AI Tsunami: NVIDIA's GPUs are the de-facto 'gold standard' for AI training and inference, capturing over 90% of the data center accelerator market. \n2. CUDA Software Moat: The proprietary CUDA software stack creates deep developer lock-in, making it difficult for competitors to displace NVIDIA hardware. \n3. Sovereign AI: Nations are increasingly building domestic AI clouds, creating a massive, non-hyperscaler revenue stream.",
        "bear-case": "1. Digestion Risk: After massive 'build-ahead' cycles, hyperscalers might enter a period of spending digestion. \n2. Custom Silicon Competition: Major clients like GOOGL, AMZN, and MSFT are developing their own AI chips (TPUs, Inferentia) to reduce reliance on NVIDIA. \n3. Valuation Sensitivity: Record-high profitability leaves little room for earnings misses in a highly anticipated market.",
        "rivalry": "Moderate: AMD is a credible challenger, but NVIDIA maintains a significant software and ecosystem lead.",
        "supplier-power": "High: Critical reliance on TSMC for leading-edge manufacturing capacity (CoWoS).",
        "buyer-power": "Moderate: Hyperscalers are large buyers with increasing leverage through custom silicon development.",
        "threat-of-entry": "Low: High R&D barriers and the massive scale of the software ecosystem protect the incumbent.",
        "substitutes": "Low: ASICs and TPUs are the primary substitutes for specialized AI workloads."
    },
    "MSFT.US": {
        "bull-case": "1. Azure + AI Synergy: Microsoft is the primary beneficiary of the Gen-AI transition through its early integration of OpenAI across the Azure and Copilot stack. \n2. Enterprise Ubiquity: Office 365 and Windows provide a non-discretionary recurring revenue foundation with massive pricing power. \n3. Cloud Dominance: Azure continues to gain market share against AWS, buoyed by deep enterprise relationships.",
        "bear-case": "1. Regulatory Scrutiny: Massive scale and cloud dominance invite antitrust attention in the EU and US. \n2. Hardware/PC Fatigue: Slower consumer hardware cycles can periodically drag on the Windows OEM business. \n3. Execution Risk: The Gen-AI spend is massive; if ROI for corporate customers is slow to materialize, it could lead to valuation compression.",
        "rivalry": "High: Intense competition with AWS and Google Cloud in the cloud infrastructure space.",
        "supplier-power": "Low: Microsoft has massive scale and is increasingly designing its own server chips (Maia).",
        "buyer-power": "Low: Enterprise software and productivity tools have extremely high switching costs.",
        "threat-of-entry": "Low: The scale of the global data center footprint and developer ecosystem is nearly impossible to replicate.",
        "substitutes": "Low: Open-source alternatives exist but lack Microsoft's enterprise-grade support and integration."
    },
    "GOOGL.US": {
        "bull-case": "1. Search Monopoly: Google Search remains the world's most valuable advertising property with a globally dominant market share. \n2. Youtube Dominance: YouTube is the premier utility for video content, increasingly capturing connected TV (CTV) advertising budgets. \n3. TPU Vertical Integration: Google's early lead in custom AI hardware (TPUs) allows for high-efficiency internal AI workloads.",
        "bear-case": "1. AI Disruption Risk: LLM-based search (Perplexity, ChatGPT) could potentially erode the traditional 'blue link' ad model over time. \n2. Anti-Trust Litigation: Ongoing major DOJ lawsuits regarding search and ad-tech could lead to forced divestitures. \n3. Cloud Catch-up: Google Cloud still lags behind Azure and AWS in terms of overall market share and enterprise profitability.",
        "rivalry": "Moderate: Primary competition in Search (Bing/AI) and Video (TikTok/Meta).",
        "supplier-power": "Low: Broad supplier base for data center components and labor.",
        "buyer-power": "Moderate: Advertisers can shift budgets, but Google's ROI remains the benchmark for performance marketing.",
        "threat-of-entry": "Moderate: Barrier to entry for AI-first search is lower than traditional crawl-based search.",
        "substitutes": "Moderate: Amazon (retail search), TikTok (discovery), and LLMs (answer engines)."
    },
    "TSLA.US": {
        "bull-case": "1. EV Cost Leadership: Tesla maintains the best margins in the industry due to its vertical integration and manufacturing innovations (Giga-casting). \n2. FSD & AI Optionality: The real 'moat' lies in Full Self-Driving (FSD) data and the Dojo supercomputer, with licensing potential as a future catalyst. \n3. Energy Ecosystem: Tesla Energy (Megapack/Powerwall) is growing faster than the automotive segment and represents a massive utility-scale opportunity.",
        "bear-case": "1. Competitive Intensity: Increasing pressure from BYD and legacy OEMs in China and Europe is forcing price cuts. \n2. Key Person Dependency: Elon Musk's focus on X (Twitter) and other ventures creates a perceived leadership gap/distraction risk. \n3. Capex Intensity: Scaling new models (Cybercab, low-cost platform) requires massive capital and carries execution risk.",
        "rivalry": "High: Intense competition from BYD, Xiaomi, and Chinese EV startups.",
        "supplier-power": "Moderate: Direct sourcing of battery minerals (Lithium) reduces power, but reliance on Nvidia for FSD compute.",
        "buyer-power": "Moderate: Consumers have an increasing number of EV choices at multiple price points.",
        "threat-of-entry": "Moderate: Software-defined vehicles have lowered the mechanical bar, but the charging network moat remains strong.",
        "substitutes": "Low: Public transit and internal combustion engines (ICE) are the primary, though fading, substitutes."
    }
}

if __name__ == "__main__":
    for ticker, pillars in data.items():
        update_ticker_pillars(ticker, pillars)
