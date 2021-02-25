# -*- coding: utf-8 -*-
from flask import Flask, render_template
import sys

app = Flask(__name__)


@app.route('/', methods=['GET'])
def webhook():
    return render_template('index.html')


def log(message):
    print(str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)