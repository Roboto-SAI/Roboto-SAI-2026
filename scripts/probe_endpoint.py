import urllib.request
import ssl

BACKEND_URL = "https://roboto-sai-backend.onrender.com"
ENDPOINT = f"{BACKEND_URL}/api/create-checkout-session"

def main():
    print(f"Probing {ENDPOINT}...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # Sending empty POST to see if we get 422 (Validation Error) or 404 (Not Found)
        req = urllib.request.Request(ENDPOINT, method="POST")
        with urllib.request.urlopen(req, context=ctx) as response:
            print(f"Status: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Return Code: {e.code}")
        if e.code == 404:
            print("❌ Endpoint NOT FOUND (Likely running old code)")
        elif e.code == 422:
            print("✅ Endpoint Exists (Running new code!)")
        else:
            print(f"Unexpected status: {e.code}")
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    main()
