import os
import json

steps = {
    "137": "ISRG.US",
    "138": "NVO.US",
    "139": "ROG.SW",
    "140": "ZTS.US"
}

base_dir = r"C:\Users\Administrator\.gemini\antigravity\brain\597de06b-f91a-47c9-b1c7-1d6f6c739d73\.system_generated\steps"

for step, ticker in steps.items():
    f_path = os.path.join(base_dir, step, "output.txt")
    if os.path.exists(f_path):
        try:
            with open(f_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Parse as JSON
                data = json.loads(content)
                general = data.get("General", {})
                name = general.get("Name", "N/A")
                desc = general.get("Description", "N/A")
                sector = general.get("Sector", "N/A")
                industry = general.get("Industry", "N/A")
                officers = general.get("Officers", {})
                
                print(f"Step {step} -> Ticker: {ticker}")
                print(f"  Name: {name}")
                print(f"  Sector: {sector}")
                print(f"  Industry: {industry}")
                print(f"  Desc (first 100 chars): {desc[:100]}...")
                print(f"  Officers Count: {len(officers)}")
                if officers:
                    # Let's print the first officer details
                    first_key = list(officers.keys())[0]
                    print(f"  First Officer Example: {officers[first_key]}")
        except Exception as e:
            print(f"Error parsing step {step}: {e}")
    else:
        print(f"Step {step} path does not exist!")
