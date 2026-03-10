import asyncio
import os
import sys
import subprocess

def run_script(script_name):
    print(f"--- Running {script_name} ---")
    try:
        # Use absolute path relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, script_name)
        
        # Use sys.executable to ensure we use the same python interpreter
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Error running {script_name}: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running {script_name}: {e}")
        return False

async def main():
    print("Starting full project initialization...")
    
    scripts = [
        "seed_category_configs.py",
        "seed_ai_providers.py",
        "seed_ollama_provider.py",
        "seed_sources.py"
    ]
    
    success = True
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    for script in scripts:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            if not run_script(script):
                success = False
        else:
            print(f"Warning: {script_path} not found, skipping.")
            
    if success:
        print("Initialization completed successfully!")
    else:
        print("Initialization completed with some errors. Check logs above.")

if __name__ == "__main__":
    asyncio.run(main())
