import sys
import os
from jinja2 import Environment, FileSystemLoader

sys.path.append(os.getcwd())

def verify_template(template_path):
    env = Environment(loader=FileSystemLoader("backend/app/templates"))
    try:
        # Just parsing should trigger syntax errors
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        env.parse(content)
        print(f"✅ Template {template_path} syntax is valid.")
    except Exception as e:
        print(f"❌ Template syntax error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_template("backend/app/templates/admin_jobs.html")
