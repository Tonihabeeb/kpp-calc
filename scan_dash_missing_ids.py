import os
import re
import ast

DASH_APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dash_app.py')


def extract_ids_from_source(source):
    id_regex = re.compile(r'id\s*=\s*["\']([\w\-]+)["\']')
    return set(id_regex.findall(source))

def extract_callback_ids_from_source(source):
    input_output_state_regex = re.compile(r'(Input|Output|State)\s*\(\s*["\']([\w\-]+)["\']')
    return set(m.group(2) for m in input_output_state_regex.finditer(source))

def scan_dash_file():
    print(f"Scanning {DASH_APP_FILE} for Dash callbacks and layout IDs...")
    try:
        with open(DASH_APP_FILE, encoding='utf-8') as file:
            src = file.read()
        layout_ids = extract_ids_from_source(src)
        callback_ids = extract_callback_ids_from_source(src)
        missing = callback_ids - layout_ids
        print("\n=== Dash Callback ID Scan (dash_app.py) ===")
        if missing:
            print("IDs referenced in callbacks but missing from layout:")
            for mid in sorted(missing):
                print(f"  - {mid}")
        else:
            print("No missing callback IDs detected.")
    except Exception as e:
        print(f"[WARN] Could not read {DASH_APP_FILE}: {e}")

def scan_flask_fastapi_routes():
    route_regex = re.compile(r'@app\.route\(["\'](.*?)["\']')
    fastapi_regex = re.compile(r'@(app|router)\.(get|post|put|delete|patch)\(["\'](.*?)["\']')
    print("\n=== Flask/FastAPI Endpoint Scan (dash_app.py) ===")
    try:
        with open(DASH_APP_FILE, encoding='utf-8') as file:
            src = file.read()
        flask_routes = route_regex.findall(src)
        fastapi_routes = fastapi_regex.findall(src)
        if flask_routes or fastapi_routes:
            print(f"{DASH_APP_FILE}:")
            for r in flask_routes:
                print(f"  Flask route: {r}")
            for r in fastapi_routes:
                print(f"  FastAPI route: /{r[2]} [{r[1].upper()}]")
        else:
            print("No Flask or FastAPI routes found in dash_app.py.")
    except Exception as e:
        print(f"[WARN] Could not read {DASH_APP_FILE}: {e}")

def main():
    print("Starting scan for Dash/Flask/FastAPI issues in dash_app.py...")
    scan_dash_file()
    scan_flask_fastapi_routes()
    print("Scan complete.")

if __name__ == "__main__":
    main() 