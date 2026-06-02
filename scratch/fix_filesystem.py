import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path("c:/Users/Administrator/Documents/kasonaops/presentation/")
OUTPUT_DIR = BASE_DIR / "output"
BACKUP_DIR = BASE_DIR / "output_backup"

# Ensure backup directory exists
BACKUP_DIR.mkdir(exist_ok=True)

# List of case mismatches from check_case.py output
case_mismatches = [
    ("0855_hk_presentation.pdf", "0855_HK_presentation.pdf"),
    ("1sxp_de_presentation.pdf", "1SXP_DE_presentation.pdf"),
    ("arenit_st_presentation.pdf", "ARENIT_ST_presentation.pdf"),
    ("asker_st_presentation.pdf", "ASKER_ST_presentation.pdf"),
    ("aspo_he_presentation.pdf", "ASPO_HE_presentation.pdf"),
    ("banb_sw_presentation.pdf", "BANB_SW_presentation.pdf"),
    ("bnzl_lse_presentation.pdf", "BNZL_LSE_presentation.pdf"),
    ("bro_us_presentation.pdf", "BRO_US_presentation.pdf"),
    ("desn_sw_presentation.pdf", "DESN_SW_presentation.pdf"),
    ("hims_us_presentation.pdf", "HIMS_US_presentation.pdf"),
    ("hlma_lse_presentation.pdf", "HLMA_LSE_presentation.pdf"),
    ("imcd_as_presentation.pdf", "IMCD_AS_presentation.pdf"),
    ("indt_st_presentation.pdf", "INDT_ST_presentation.pdf"),
    ("klar_us_presentation.pdf", "KLAR_US_presentation.pdf"),
    ("lly_us_presentation.pdf", "LLY_US_presentation.pdf"),
    ("medp_us_presentation.pdf", "MEDP_US_presentation.pdf"),
    ("ppgn_sw_presentation.pdf", "PPGN_SW_presentation.pdf"),
    ("qxo_us_presentation.pdf", "QXO_US_presentation.pdf"),
    ("rovi_mc_presentation.pdf", "ROVI_MC_presentation.pdf"),
    ("stvn_us_presentation.pdf", "STVN_US_presentation.pdf"),
    ("wst_us_presentation.pdf", "WST_US_presentation.pdf"),
    ("ypsn_sw_presentation.pdf", "YPSN_SW_presentation.pdf"),
    ("zeal_co_presentation.pdf", "ZEAL_CO_presentation.pdf"),
]

def rename_files():
    print("--- RENAMING CASE MISMATCHES ---")
    for actual, expected in case_mismatches:
        actual_path = OUTPUT_DIR / actual
        expected_path = OUTPUT_DIR / expected
        
        if actual_path.exists():
            print(f"Renaming: {actual} -> {expected}")
            # Use temporary name to avoid issues on case-insensitive filesystems
            temp_path = OUTPUT_DIR / (actual + ".tmp")
            actual_path.rename(temp_path)
            temp_path.rename(expected_path)
        else:
            print(f"File not found: {actual}")

def cleanup_extras():
    print("\n--- CLEANING UP EXTRA FILES ---")
    # This list is based on the check_case.py output for "EXTRA FILES"
    # We move them to backup instead of deleting
    
    all_files = list(OUTPUT_DIR.glob("*"))
    # We want to keep only the "Expected" format files in the main output dir
    # A simple way is to define what we want to KEEP or what we want to MOVE.
    # For now, let's move files that contain "de_presentation" or have a dash in the ticker part
    
    for file_path in all_files:
        if file_path.is_dir():
            continue
            
        filename = file_path.name
        
        # Criteria for moving to backup:
        # 1. Contains "_de_presentation"
        # 2. Lowercase tickers (except those we just renamed)
        # 3. Files with dashes in the name (e.g. ADDT-B.ST_presentation.pdf)
        
        should_move = False
        if "_de_presentation" in filename:
            should_move = True
        elif any(c.islower() for c in filename.split('_')[0]) and not filename.startswith("0855_hk"): # basic check for lowercase ticker
             # If it's one of the ones we renamed, we already handled it.
             # Actually, if any lowercase letter in the prefix, it's likely an extra.
             should_move = True
        elif "-" in filename.split('_')[0]:
            should_move = True
        elif filename.endswith("_presentation.md") and any(c.islower() for c in filename.split('_')[0]):
            should_move = True

        if should_move:
            print(f"Moving to backup: {filename}")
            shutil.move(str(file_path), str(BACKUP_DIR / filename))

if __name__ == "__main__":
    rename_files()
    cleanup_extras()
    print("\nDone.")
