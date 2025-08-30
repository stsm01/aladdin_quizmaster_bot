#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN не задан в окружении")

resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=10)
resp.raise_for_status()
data = resp.json()
if not data.get("ok"):
    raise SystemExit(f"getMe error: {data}")

me = data["result"]
print(f"id={me.get('id')} username=@{me.get('username')} name={me.get('first_name')}")


