import os

steps_dir = r"C:\Users\Administrator\.gemini\antigravity\brain\597de06b-f91a-47c9-b1c7-1d6f6c739d73\.system_generated\steps"
if os.path.exists(steps_dir):
    print(f"Steps directory exists: {steps_dir}")
    subdirs = os.listdir(steps_dir)
    print(f"Subdirectories inside steps: {subdirs}")
    for subdir in subdirs:
        sub_path = os.path.join(steps_dir, subdir)
        if os.path.isdir(sub_path):
            files = os.listdir(sub_path)
            print(f"  Step {subdir} contains: {files}")
            # check if there's any file containing fundamentals data
            for f in files:
                f_path = os.path.join(sub_path, f)
                if os.path.isfile(f_path) and os.path.getsize(f_path) > 100:
                    with open(f_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                        line = file_obj.readline()
                        print(f"    - {f} (size={os.path.getsize(f_path)}): {line[:100].strip()}...")
else:
    print(f"Steps directory DOES NOT exist: {steps_dir}")
