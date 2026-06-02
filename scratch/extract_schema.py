import os
import json

path = r"C:\Users\Administrator\.gemini\antigravity\brain\e7d98d56-c489-401e-881d-93f758fd3a67\.system_generated\steps\480\output.txt"
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

for table in data['tables']:
    if table['name'] == 'public.company_presentation':
        print(json.dumps(table, indent=2))
        break
