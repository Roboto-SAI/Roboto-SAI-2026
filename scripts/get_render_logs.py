import urllib.request
import json

API_KEY = "rnd_XsghJb1MQUDYcjQwVsIu77evDsVs"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
BASE_URL = "https://api.render.com/v1"

def make_request(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def main():
    services = make_request(f"{BASE_URL}/services?limit=50")
    if not services: return

    svc_id = None
    for s in services:
        if s['service']['name'] == 'roboto-sai-backend':
            svc_id = s['service']['id']
            break
    
    if svc_id:
        deploys = make_request(f"{BASE_URL}/services/{svc_id}/deploys?limit=1")
        if deploys and len(deploys) > 0:
            print(json.dumps(deploys[0], indent=2))
        else:
            print("NO_DEPLOYS")

if __name__ == "__main__":
    main()
