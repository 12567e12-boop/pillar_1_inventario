import requests
import json

url = "http://localhost:8001/api/productos/?especialidad=plomeria"
try:
    print(f"Fetching {url}...")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print("JSON Response:")
        print(json.dumps(data, indent=2))
    except:
        print("Raw Content:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
