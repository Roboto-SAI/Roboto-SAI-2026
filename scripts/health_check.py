import urllib.request
import json
import ssl

BACKEND_URL = "https://roboto-sai-backend.onrender.com"
ENDPOINT = f"{BACKEND_URL}/api/health"

def main():
    print(f"Checking health at: {ENDPOINT}")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE # For debugging if cert issues arise

    try:
        req = urllib.request.Request(ENDPOINT)
        with urllib.request.urlopen(req, context=ctx) as response:
            status = response.status
            data = response.read().decode()
            print(f"Status: {status}")
            print(f"Response: {data}")
            
            if status == 200:
                print("PASSED: Backend is HEALTHY")
            else:
                print("FAILED: Backend returned non-200 status")

    except Exception as e:
        print(f"ERROR: Verification Failed: {e}")

if __name__ == "__main__":
    main()
