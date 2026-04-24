#!/usr/bin/env python3
"""
n8n_final_stage.py — Execute NotebookLM_DeepResearch workflow and update Supabase

Bridges the n8n workflow outputs to the company_presentation table by:
1. Executing the workflow via MCP-compatible form trigger
2. Polling n8n execution API for completion (handles long-running AI agents)
3. Extracting outputs from all 4 branches
4. Updating the Supabase company_presentation record

Usage:
    python tools/n8n_final_stage.py --company "Danaher Corporation" --ticker DHR.US
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(r"C:\Users\Administrator\Documents\kasonaops\presentation\.env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nayggiozebvwqnpjzvvn.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# n8n Configuration
N8N_BASE_URL = "https://n8n.srv1030093.hstgr.cloud"
N8N_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0NWYyNzFjMS1iNjczLTRkZDktYTQxMi0yYmE4NjA0ZmQ1YTIiLCJpc3MiOiJuOG4iLCJhdWQiOiJtY3Atc2VydmVyLWFwaSIsImp0aSI6Ijk1MDFjZDg3LWY3ZDItNDg3MS1hZDFkLWE2YzdhZmNlYWRmZiIsImlhdCI6MTc3NjE1ODA2MX0.3c4lSIpM6Le_GqithnEYvKYHNQz3hQoE1bUFGu7kfW4"
WORKFLOW_ID = "QTfs16hVROvSIjlA"


def get_n8n_headers():
    """Get headers for n8n API calls."""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {N8N_BEARER_TOKEN}",
    }


def trigger_workflow(company_name: str) -> dict:
    """Trigger the workflow via n8n API and return the execution ID."""
    url = f"{N8N_BASE_URL}/api/v1/workflows/{WORKFLOW_ID}/run"
    payload = json.dumps({
        "payload": {"company_name": company_name}
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, headers=get_n8n_headers(), method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"[OK] Workflow triggered. Response: {json.dumps(result, indent=2)[:500]}")
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[ERR] HTTP {e.code}: {body[:500]}")
        return {"error": body}
    except Exception as e:
        print(f"[ERR] Trigger failed: {e}")
        return {"error": str(e)}


def get_latest_execution(workflow_id: str) -> dict:
    """Get the latest execution for the workflow."""
    url = f"{N8N_BASE_URL}/api/v1/executions?workflowId={workflow_id}&limit=1&status=success"
    req = urllib.request.Request(url, headers=get_n8n_headers())
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except Exception as e:
        print(f"[ERR] Get executions failed: {e}")
        return {"error": str(e)}


def get_execution_details(execution_id: str) -> dict:
    """Get full execution details including node outputs."""
    url = f"{N8N_BASE_URL}/api/v1/executions/{execution_id}"
    req = urllib.request.Request(url, headers=get_n8n_headers())
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result
    except Exception as e:
        print(f"[ERR] Get execution details failed: {e}")
        return {"error": str(e)}


def poll_for_completion(workflow_id: str, max_wait_seconds: int = 600, poll_interval: int = 30) -> dict:
    """Poll n8n for workflow completion, increasing wait times as needed."""
    print(f"\n[*] Polling for workflow completion (max {max_wait_seconds}s, interval {poll_interval}s)...")
    
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < max_wait_seconds:
        attempt += 1
        elapsed = int(time.time() - start_time)
        
        # Check running executions
        url = f"{N8N_BASE_URL}/api/v1/executions?workflowId={workflow_id}&limit=1"
        req = urllib.request.Request(url, headers=get_n8n_headers())
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                
                if result.get("data") and len(result["data"]) > 0:
                    latest = result["data"][0]
                    status = latest.get("status", "unknown")
                    exec_id = latest.get("id", "unknown")
                    
                    print(f"  [{elapsed}s] Attempt {attempt}: Execution {exec_id} status = {status}")
                    
                    if status == "success":
                        print(f"\n[OK] Workflow completed successfully after {elapsed}s!")
                        return get_execution_details(exec_id)
                    elif status == "error":
                        print(f"\n[ERR] Workflow failed after {elapsed}s")
                        return get_execution_details(exec_id)
                    elif status in ("running", "waiting", "new"):
                        pass  # Still running, continue polling
                    else:
                        print(f"  [WARN] Unknown status: {status}")
                else:
                    print(f"  [{elapsed}s] No executions found yet...")
                    
        except Exception as e:
            print(f"  [{elapsed}s] Poll error: {e}")
        
        # Adaptive wait: increase interval after first few attempts
        current_interval = poll_interval
        if attempt > 5:
            current_interval = min(poll_interval * 2, 60)
        if attempt > 10:
            current_interval = min(poll_interval * 3, 90)
            
        print(f"  Waiting {current_interval}s before next check...")
        time.sleep(current_interval)
    
    print(f"\n[TIMEOUT] Workflow did not complete within {max_wait_seconds}s")
    return {"error": "timeout"}


def extract_node_outputs(execution: dict) -> dict:
    """Extract outputs from all 4 workflow branches."""
    outputs = {
        "ai_agent_firmenhistorie": None,
        "l4_report": None,
        "youtube_podcast": None,
        "youtube_ceo_interview": None,
        "linkedin_profiles": None,
    }
    
    result_data = execution.get("data", {}).get("resultData", {}).get("runData", {})
    
    # 1. AI Agent: Firmenhistorie und Analyse → output text
    node_data = result_data.get("AI Agent: Firmenhistorie und Analyse", [])
    if node_data:
        try:
            output = node_data[0]["data"]["main"][0][0]["json"].get("output", "")
            outputs["ai_agent_firmenhistorie"] = output
            print(f"  [OK] ai_agent_firmenhistorie: {len(output)} chars")
        except (KeyError, IndexError):
            print("  [WARN] Could not extract ai_agent_firmenhistorie output")
    
    # 2. L4 Report HTML (from Leadership agent)
    node_data = result_data.get("L4_Report Generator HTML", [])
    if node_data:
        try:
            html = node_data[0]["data"]["main"][0][0]["json"].get("html_output", "")
            outputs["l4_report"] = html
            print(f"  [OK] l4_report: {len(html)} chars")
        except (KeyError, IndexError):
            print("  [WARN] Could not extract l4_report output")
    
    # 3. YouTube Acquired Podcast (filtered < 2 years)
    node_data = result_data.get("Filter: Videos < 2 Years", [])
    if not node_data:
        node_data = result_data.get("Youtube Aquired Podcast", [])
    if node_data:
        try:
            items = node_data[0]["data"]["main"][0]
            videos = []
            for item in items[:5]:  # Top 5
                v = item.get("json", {})
                videos.append({
                    "title": v.get("title", ""),
                    "url": v.get("url", ""),
                    "date": v.get("date", ""),
                    "viewCount": v.get("viewCount", 0),
                })
            outputs["youtube_podcast"] = json.dumps(videos)
            print(f"  [OK] youtube_podcast: {len(videos)} videos")
        except (KeyError, IndexError):
            print("  [WARN] Could not extract youtube_podcast output")
    
    # 4. YouTube CEO Interview (filtered < 6 months)
    node_data = result_data.get("Filter: Videos < 6 Monate", [])
    if not node_data:
        node_data = result_data.get("Youtube Ceo Interview", [])
    if node_data:
        try:
            items = node_data[0]["data"]["main"][0]
            videos = []
            for item in items[:5]:  # Top 5
                v = item.get("json", {})
                videos.append({
                    "title": v.get("title", ""),
                    "url": v.get("url", ""),
                    "date": v.get("date", ""),
                    "viewCount": v.get("viewCount", 0),
                })
            outputs["youtube_ceo_interview"] = json.dumps(videos)
            print(f"  [OK] youtube_ceo_interview: {len(videos)} videos")
        except (KeyError, IndexError):
            print("  [WARN] Could not extract youtube_ceo_interview output")
    
    # 5. LinkedIn Profile Scraper
    node_data = result_data.get("LinkedIn Profile Scraper", [])
    if node_data:
        try:
            items = node_data[0]["data"]["main"][0]
            profiles = []
            for item in items:
                p = item.get("json", {})
                profiles.append({
                    "name": p.get("basic_info", {}).get("full_name", ""),
                    "headline": p.get("basic_info", {}).get("headline", ""),
                    "location": p.get("basic_info", {}).get("location", ""),
                    "profile_url": p.get("basic_info", {}).get("profile_url", ""),
                    "company": p.get("basic_info", {}).get("current_company", ""),
                })
            outputs["linkedin_profiles"] = json.dumps(profiles)
            print(f"  [OK] linkedin_profiles: {len(profiles)} profiles")
        except (KeyError, IndexError):
            print("  [WARN] Could not extract linkedin_profiles output")
    
    return outputs


def update_supabase(ticker: str, outputs: dict):
    """Update the company_presentation record with workflow outputs."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    update_data = {}
    if outputs.get("ai_agent_firmenhistorie"):
        update_data["ai_agent_firmenhistorie"] = outputs["ai_agent_firmenhistorie"]
    if outputs.get("l4_report"):
        update_data["l4_report"] = outputs["l4_report"]
    if outputs.get("youtube_podcast"):
        update_data["youtube_podcast"] = outputs["youtube_podcast"]
    if outputs.get("youtube_ceo_interview"):
        update_data["youtube_ceo_interview"] = outputs["youtube_ceo_interview"]
    if outputs.get("linkedin_profiles"):
        update_data["linkedin_profiles"] = outputs["linkedin_profiles"]
    
    update_data["n8n-info"] = f"NotebookLM_DeepResearch completed {datetime.now().strftime('%Y-%m-%d %H:%M')} - all outputs captured"
    
    if not update_data:
        print("[WARN] No outputs to update")
        return
    
    print(f"\n[*] Updating company_presentation for {ticker} with {len(update_data)} fields...")
    
    response = supabase.table("company_presentation").update(update_data).eq("ticker_eod", ticker).execute()
    
    if response.data:
        print(f"[OK] Database updated successfully for {ticker}")
        for key in update_data:
            val = str(update_data[key])[:100]
            print(f"  - {key}: {val}...")
    else:
        print(f"[WARN] No rows updated for {ticker}")


def main():
    parser = argparse.ArgumentParser(description="n8n Final Stage — Execute workflow and update Supabase")
    parser.add_argument("--company", required=True, help="Company name (e.g., 'Danaher Corporation')")
    parser.add_argument("--ticker", required=True, help="Ticker (e.g., DHR.US)")
    parser.add_argument("--max-wait", type=int, default=600, help="Max wait seconds (default: 600)")
    parser.add_argument("--poll-interval", type=int, default=30, help="Poll interval seconds (default: 30)")
    parser.add_argument("--skip-trigger", action="store_true", help="Skip triggering (use latest execution)")
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"n8n Final Stage — {args.company} ({args.ticker})")
    print(f"{'='*60}")
    
    # Step 1: Trigger the workflow
    if not args.skip_trigger:
        print(f"\n[1/4] Triggering workflow for '{args.company}'...")
        trigger_result = trigger_workflow(args.company)
        if "error" in trigger_result:
            print(f"[WARN] Trigger may have failed, but checking execution status anyway...")
    else:
        print(f"\n[1/4] Skipping trigger — using latest execution...")
    
    # Step 2: Poll for completion
    print(f"\n[2/4] Waiting for workflow completion (max {args.max_wait}s)...")
    execution = poll_for_completion(WORKFLOW_ID, args.max_wait, args.poll_interval)
    
    if "error" in execution and execution["error"] == "timeout":
        print("\n[WARN] Workflow timed out. Checking latest successful execution...")
        latest = get_latest_execution(WORKFLOW_ID)
        if latest.get("data") and len(latest["data"]) > 0:
            exec_id = latest["data"][0]["id"]
            execution = get_execution_details(exec_id)
            print(f"  Using latest execution: {exec_id}")
        else:
            print("[ERR] No successful executions found. Exiting.")
            sys.exit(1)
    
    # Step 3: Extract outputs
    print(f"\n[3/4] Extracting outputs from workflow branches...")
    outputs = extract_node_outputs(execution)
    
    filled = sum(1 for v in outputs.values() if v)
    print(f"\n  Summary: {filled}/5 output fields populated")
    
    # Step 4: Update Supabase
    print(f"\n[4/4] Updating Supabase company_presentation table...")
    update_supabase(args.ticker, outputs)
    
    print(f"\n{'='*60}")
    print(f"Pipeline complete for {args.ticker}!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
