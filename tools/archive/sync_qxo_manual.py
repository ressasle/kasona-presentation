import os
import json
from supabase import create_client
from dotenv import load_dotenv

def sync():
    # Load .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(url, key)
    
    data_path = "output/QXO_Inc._data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Manually fix the l4_report error
    data["l4_report"] = (
        "QXO Inc. represents a high-conviction 'platform build-out' led by serial industrialist Brad Jacobs. "
        "The company's core value proposition lies in the 'Jacobs Playbook'—combining aggressive, accretive M&A "
        "with a unified, state-of-the-art technological platform to consolidate the fragmented $800B building "
        "products distribution market. With a $5B+ cash position and a leadership team comprised of proven "
        "XPO/GXO veterans, QXO is uniquely positioned to capture massive scale advantages in procurement and logistics. "
        "While the stock currently trades at a significant speculative premium based on Jacobs' reputation, "
        "the successful integration of its first multi-billion dollar platform acquisitions will be the primary catalyst "
        "for long-term outperformance. Risks are elevated due to key-person dependency and the cyclical nature of "
        "construction, but the technological moat and capital allocation efficiency make it a standout institutional-grade consolidator."
    )
    
    payload = {
        "history-evolution":       data.get("history-evolution", ""),
        "leadership-governance":   data.get("leadership-governance", ""),
        "risk-success-factors":    data.get("risk-success-factors", ""),
        "bull-case":               data.get("bull-case", ""),
        "bear-case":               data.get("bear-case", ""),
        "rivalry":                 data.get("rivalry", ""),
        "supplier-power":          data.get("supplier-power", ""),
        "buyer-power":             data.get("buyer-power", ""),
        "threat-of-entry":         data.get("threat-of-entry", ""),
        "substitutes":             data.get("substitutes", ""),
        "linkedin_profiles":       data.get("linkedin_profiles", []),
        "l4_report":               data.get("l4_report", ""),
        "youtube_ceo_interview":   data.get("youtube_ceo_interview", ""),
        "youtube_podcast":         data.get("youtube_podcast", ""),
        "ai_agent_firmenhistorie": data.get("history-evolution", ""), # keep sync with legacy if needed
        "status":                  "to_review"
    }
    
    ticker = "QXO.US"
    print(f"Syncing {ticker}...")
    res = supabase.table("company_presentation").update(payload).eq("ticker_eod", ticker).execute()
    
    if len(res.data) > 0:
        print(f"Success! Updated {ticker}")
    else:
        print(f"Failed to update {ticker}")

if __name__ == "__main__":
    sync()
