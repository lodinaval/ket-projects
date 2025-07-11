import os, re, smtplib, time, argparse, json, requests, schedule, cloudscraper
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)
COL = {
    "INFO" : Fore.GREEN,
    "WARN" : Fore.YELLOW,
    "ERROR" : Fore.RED
}
ORDER = ("ERROR", "WARN", "INFO")
SCRAPER = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    }
)

def load_config():
    load_dotenv()
    cli = argparse.ArgumentParser(
        description="Mails Grow A Garden Stock"
    )
    cli.add_argument(
        "--interval", type=int, help = "minutes between emails"
    )
    args = cli.parse_args()
    
    cfg = {
        "GMAIL_USER" : os.getenv("GMAIL_USER"),
        "GMAIL_APP_PASS" : os.getenv("GMAIL_APP_PASSWORD"),
        "RECIPIENT_EMAIL" : os.getenv("RECIPIENT_EMAIL"),
        "STOCK_URL" : os.getenv("STOCK_URL"),
        "CHECK_INTERVAL" : int(os.getenv("CHECK_INTERVAL", 5)),
        "LOG_LEVEL" : os.getenv("LOG_LEVEL", "INFO").upper(),
        "WEBHOOK_URL": os.getenv("WEBHOOK_URL")
    }
    return cfg
    
def log(level, msg):
    if ORDER.index(level)<=ORDER.index(CONFIG["LOG_LEVEL"]):
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{COL[level]}[{now}] {level}: {msg}{Style.RESET_ALL}")
        
def get_stock():
    url = "https://api.joshlei.com/v2/growagarden/stock"
    log("INFO", f"Calling Joshlei API: {url}")
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
    except Exception as e:
        log("ERROR", f"Calling Joshlei API Failed: {e}")
        return tuple()
    
    data = res.json()
    seeds = data.get("seed_stock", [])
    return seeds

old_seeds = ()

def send_discord_webhook(seed_list : list[dict]):
    url = CONFIG.get("WEBHOOK_URL")
    fields = [
        {"name": item["display_name"], "value": str(item["quantity"]), "inline": True}
        for item in old_seeds
    ]

    embed = {
        "title": "🌱 Ket's Seed Stock",
        "color": 0x00FF00,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": fields
    }

    payload = {"embeds": [embed]}
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
    except Exception as e:
        log("ERROR", f"Failed to send discord webhook: {e}")

def changes_in_stock():
    global old_seeds
    new_seeds = get_stock()
    if(old_seeds!=new_seeds):
        log("INFO", "New Seeds Are Out!")
        old_seeds = new_seeds
        send_discord_webhook(old_seeds)
    else:
        log("INFO", "No stock change")
        

if __name__ == "__main__":
    CONFIG = load_config()
    seed_stock_updated = changes_in_stock()
    schedule.every(CONFIG["CHECK_INTERVAL"]).seconds.do(changes_in_stock)
    while True: #this while loop needs to be here for schedule to work
        schedule.run_pending()
        time.sleep(1)

    
    