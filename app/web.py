# -*- coding: utf-8 -*-
from flask import Flask, render_template
import sys
import pandas as pd
import os

app = Flask(__name__)

DIR = os.path.dirname(os.path.realpath(__file__))


@app.route('/', methods=['GET'])
def webhook():
    return render_template('template.html', df=pd.read_csv('./static/data.csv'))


def log(message):
    print(str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)