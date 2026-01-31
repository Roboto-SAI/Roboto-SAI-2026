import urllib.request
import json
import os

API_KEY = "rnd_XsghJb1MQUDYcjQwVsIu77evDsVs"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
BASE_URL = "https://api.render.com/v1"

def make_request(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode())
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("Fetching services...")
    services = make_request(f"{BASE_URL}/services?limit=50")
    if not services: return

    backend_svc = None
    for s in services:
        if s['service']['name'] == 'roboto-sai-backend':
            backend_svc = s['service']
            break
    
    if not backend_svc:
        print("Backend service 'roboto-sai-backend' not found.")
        return

    svc_id = backend_svc['id']
    print(f"Found Service: {backend_svc['name']} ({svc_id})")

    print(f"Fetching latest deploy...")
    deploys = make_request(f"{BASE_URL}/services/{svc_id}/deploys?limit=1")
    
    if not deploys:
        print("No deploys found.")
        return

    latest = deploys[0]
    deploy_id = latest['id']
    status = latest['status']
    print(f"Latest Deploy: {deploy_id} | Status: {status}")
    
    commit = latest.get('commit', {})
    print(f"Commit: {commit.get('message')} ({commit.get('id')})")

if __name__ == "__main__":
    main()
