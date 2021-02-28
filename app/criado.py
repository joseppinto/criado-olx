import json
import os
import sys

import jinja2
import lxml.html
import pandas as pd
import requests
from flask import Flask
from sqlalchemy import create_engine

app = Flask(__name__)

# CONFIGS
DIR = os.path.dirname(os.path.realpath(__file__))
WISHLIST_FILE = f'{DIR}/wishlist.txt'
WISHLIST = [x for x in open(WISHLIST_FILE, "r").readlines()]
HTML_PAGE_PATH = f'{DIR}/templates/index.html'

MESSENGER_ID = os.environ["MESSENGER_ID"]
MESSENGER_PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]

DATABASE_URL = os.environ["DATABASE_URL"]
ADS_TABLE_NAME = 'ads'
ENGINE = create_engine(DATABASE_URL)
CONN = ENGINE.connect()

# FLASK ROUTES
if __name__ == '__main__':
    app.run(debug=True)


@app.route('/', methods=['GET'])
def webhook():
    return render_template('index.html')


@app.route('/update', methods=['GET'])
def update():
    criado()
    return 'OK', 200


# BOT LOGIC
def criado():
    results = {
        'item': [],
        'url': [],
        'title': [],
        'price': []
    }
    df = pd.DataFrame(columns=['item', 'url', 'title', 'price'])
    try:
        df = pd.read_sql(f'select * from "{ADS_TABLE_NAME}"', CONN)
    except Exception as e:
        print(e)

    df = df[df['item'].isin(WISHLIST)]

    for item in WISHLIST:
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

    new_ads_flag = len(results['url']) > 0
    if new_ads_flag:
        df = pd.concat([df, pd.DataFrame(results)], axis=0).sort_values(['price'])
        df.to_sql(ADS_TABLE_NAME, CONN, if_exists='replace')
        message_results(results)
    print_index(df, new_ads_flag)
    print(f"Found {len(results['url'])} ads")


# UTILS
def save_ad(r, item, url, title, price):
    r['item'].append(item)
    r['url'].append(url)
    r['title'].append(title)
    r['price'].append(price)


def render_template(file_name, **context):
    return jinja2.Environment(loader=jinja2.FileSystemLoader(f"{DIR}/templates/")) \
        .get_template(file_name) \
        .render(context)


def print_index(df, flag):
    if not os.path.exists(HTML_PAGE_PATH) or flag:
        s = render_template('template.html', df=df)
        text_file = open(f'{DIR}/templates/index.html', "w")
        text_file.write(s)
        text_file.close()


def message_results(r):
    if len(r['url']) == 0:
        return
    message = ""
    for i in range(len(r['url'])):
        message += f"Item: {r['title'][i]}\nPreço: {r['price'][i]}\nUrl: {r['url'][i]}\n---\n"

    send_message(MESSENGER_ID, message)


def send_message(recipient_id, message_text):
    log(f"Sending message to {recipient_id}:\n {message_text}\n")

    params = {
        "access_token": MESSENGER_PAGE_ACCESS_TOKEN
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
