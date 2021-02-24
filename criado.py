import pandas as pd
import lxml.html
import requests
import smtplib
import ssl
import os
import sys

# CONFIGS
DIR = os.path.dirname(os.path.realpath(__file__))
WISHLIST_FILE = f'{DIR}/wishlist.txt'
DATA_FILE = f'{DIR}/data.csv'
SENDER_EMAIL = os.environ['SENDER_EMAIL']
SENDER_EMAIL_PASS = os.environ['SENDER_EMAIL_PASS']
RECIPIENT_EMAIL = sys.argv[1]
PORT = 587
SMTP_SERVER = "smtp.gmail.com"

# SCRIPT

# Read wishlist and database
wishlist = [x for x in open(WISHLIST_FILE, "r").readlines()]
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.read_csv(f"{DATA_FILE}.sample")

df = df[df['item'].isin(wishlist)]

results = {
    'item': [],
    'url': [],
    'title': [],
    'price': []
}


def save_ad(results, item, url, title, price):
    results['item'].append(item)
    results['url'].append(url)
    results['title'].append(title)
    results['price'].append(price)


def email_results(results):
    if len(results['url']) == 0:
        return
    message = "Novos anúncios encontrados!"
    for i in range(len(results['url'])):
        message += f"\nItem: {results['item'][i]}"
        message += f"\nPreço: {results['price'][i]}"
        message += f"\nUrl: {results['url'][i]}"
        message += f"--------------------------------"

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, PORT) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(SENDER_EMAIL, SENDER_EMAIL_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.encode())
    print(f"Email sent to {RECIPIENT_EMAIL}")


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
        price = float(price.replace("€", ""))

        if df['url'].str.contains(url).sum() == 0:
            save_ad(results, item, url, title, price)
        else:
            if df[df['url'] == url]['price'].values[0] > price:
                index = df[df['url'] == url].index
                df.drop(index, axis=0, inplace=True)
                save_ad(results, item, url, title, price)

df = pd.concat([df, pd.DataFrame(results)], axis=0)
df.to_csv(DATA_FILE, index=False)
email_results(results)
