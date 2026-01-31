import urllib.request
import json

API_KEY = "rnd_XsghJb1MQUDYcjQwVsIu77evDsVs"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
BASE_URL = "https://api.render.com/v1"

def main():
    # 1. Get Service ID
    req = urllib.request.Request(f"{BASE_URL}/services?limit=50", headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as res:
            services = json.loads(res.read().decode())
    except Exception as e:
        print(f"Error fetching services: {e}")
        return

    svc_id = None
    for s in services:
        if s['service']['name'] == 'roboto-sai-backend':
            svc_id = s['service']['id']
            break
    
    if not svc_id:
        print("Backend service not found")
        return

    # 2. Trigger Deploy
    print(f"Triggering deploy for {svc_id}...")
    url = f"{BASE_URL}/services/{svc_id}/deploys"
    data = {"clearCache": "clear"} # Clear cache to be safe
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=HEADERS, method='POST')
        with urllib.request.urlopen(req) as res:
            deploy = json.loads(res.read().decode())
            print(f"Deploy Triggered: {deploy.get('id')} Status: {deploy.get('status')}")
    except Exception as e:
        print(f"Error triggering deploy: {e}")
        # Try reading error body if possible
        pass

if __name__ == "__main__":
    main()
