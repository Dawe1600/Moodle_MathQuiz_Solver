import os
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
r = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {key}'})
if r.status_code == 200:
    for m in r.json().get('data', []):
        print(m['id'])
else:
    print("Błąd:", r.text)
