from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd
import lxml.html
import requests
import smtplib
import ssl
import os

# CONFIGS
DIR = os.path.dirname(os.path.realpath(__file__))
WISHLIST_FILE = f'{DIR}/wishlist.txt'
DATA_FILE = f'{DIR}/data.csv'
SENDER_EMAIL = os.environ['SENDER_EMAIL']
SENDER_EMAIL_PASS = os.environ['SENDER_EMAIL_PASS']
RECIPIENT_EMAIL = os.environ['RECIPIENT_EMAIL']
PORT = 587
SMTP_SERVER = "smtp.gmail.com"

# SCRIPT

# Read wishlist and database
wishlist = [x for x in open(WISHLIST_FILE, "r").readlines()]


def save_ad(r, item, url, title, price):
    r['item'].append(item)
    r['url'].append(url)
    r['title'].append(title)
    r['price'].append(price)


def email_results(r):
    if len(r['url']) == 0:
        return
    message = f"""\
        Novos anúncios encontrados!!
        """
    for i in range(len(r['url'])):
        message += f"""
        Item: {r['item'][i]}
        Preço: {r['price'][i]}
        Url: {r['url'][i]}
        -------------------------------------------
        """

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_SERVER, PORT) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(SENDER_EMAIL, SENDER_EMAIL_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.encode())
    print(f"Email sent to {RECIPIENT_EMAIL}")


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
    email_results(results)
    print(f"Found {len(results['url'])} ads")


# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(criado, "interval", seconds=60)

scheduler.start()
