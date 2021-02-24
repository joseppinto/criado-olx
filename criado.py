from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd
import lxml.html
import requests
import os
import sys
import json

# CONFIGS
DIR = os.path.dirname(os.path.realpath(__file__))
WISHLIST_FILE = f'{DIR}/wishlist.txt'
DATA_FILE = f'{DIR}/data.csv'
MESSENGER_ID = os.environ["MESSENGER_ID"]

# SCRIPT

# Read wishlist and database
wishlist = [x for x in open(WISHLIST_FILE, "r").readlines()]


def save_ad(r, item, url, title, price):
    r['item'].append(item)
    r['url'].append(url)
    r['title'].append(title)
    r['price'].append(price)


def message_results(r):
    if len(r['url']) == 0:
        return
    items = ""

    for i in range(len(r['url'])):
        items += f"""
            -------------------------------------------
        
            Item: {r['title'][i]}
            Preço: {r['price'][i]}
            Url: {r['url'][i]}
            """
    message = f"""\
        Novos anúncios encontrados!!
        
        {items}
        """
    send_message(MESSENGER_ID, message)


def criado():
    results = {
        'item': [],
        'url': [],
        'title': [],
        'price': []
    }
    df = pd.DataFrame(columns=['item', 'url', 'title', 'price'])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)

    df = df[df['item'].isin(wishlist)]

    for item in wishlist:
        search_url = 'https://www.olx.pt/ads/q-' + item.replace(" ", "-")
        r = requests.get(search_url)
        root = lxml.html.fromstring(r.content)

        ads = root.xpath("//td[contains(@class,'offer')]")

        for ad in ads:
            url = ad.xpath(".//h3/a/@href")
            if len(url) == 0:
                continue
            url = url[0]
            title = ad.xpath(".//h3/a/strong/text()")[0]
            price = ad.xpath(".//p[contains(@class,'price')]/strong/text()")[0].strip()
            price = float(price.replace("€", "").replace(",", "."))

            if df['url'].str.contains(url).sum() == 0:
                save_ad(results, item, url, title, price)
            else:
                if df[df['url'] == url]['price'].values[0] > price:
                    index = df[df['url'] == url].index
                    df.drop(index, axis=0, inplace=True)
                    save_ad(results, item, url, title, price)

    df = pd.concat([df, pd.DataFrame(results)], axis=0)
    df.to_csv(DATA_FILE, index=False)
    message_results(results)
    print(f"Found {len(results['url'])} ads")


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text.encode('utf-8')))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):
    print(str(message))
    sys.stdout.flush()

# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(criado, "interval", seconds=60)

scheduler.start()
