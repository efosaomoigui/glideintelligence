import subprocess, sys
result = subprocess.run(
    [sys.executable, "run_cluster_and_analyze.py"],
    capture_output=True, text=True, cwd=r"c:\Users\Efe-Dev\Documents\business News\glideintelligence\backend"
)
print("STDOUT:", result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
print("STDERR:", result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
print("Exit code:", result.returncode)
