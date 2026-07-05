import json
import urllib.request
import urllib.error
from config.settings import SettingsManager

settings = SettingsManager()
api_key = settings.get("ai_api_key")
print(f"Using API Key: {api_key[:10]}...{api_key[-5:]}")

url = "https://api.x.ai/v1/images/generations"
payload = {
    "model": "grok-2-image-gen",
    "prompt": "a beautiful forest",
    "n": 1,
    "resolution": "1k",
    "aspect_ratio": "1:1",
    "response_format": "url"
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    url,
    data=data,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    method="POST"
)

print("Sending request to xAI...")
try:
    with urllib.request.urlopen(req, timeout=15) as response:
        print("Success! Response:")
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"HTTP Error ({e.code}):")
    print(e.read().decode("utf-8"))
except Exception as e:
    print("Other error:", e)
