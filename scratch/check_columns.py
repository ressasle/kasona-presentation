import os
from supabase import create_client
from dotenv import load_dotenv

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Get one row to see columns
res = supabase.table("company_presentation").select("*").limit(1).execute()
if res.data:
    row = res.data[0]
    print("Columns in company_presentation:")
    for col in sorted(row.keys()):
        print(f" - {col}")
else:
    print("No data found.")
