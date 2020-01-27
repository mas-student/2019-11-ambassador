#!/usr/bin/python
# -*- coding: utf8 -*-

from json import dumps
from os import environ
from copy import deepcopy
from dataclasses import dataclass
from logging import getLogger

import requests
from dataclasses_jsonschema import JsonSchemaMixin, ValidationError
from flask import Flask, abort, render_template, request


logger = getLogger(__name__)


ONE_SIGNAL_APP_ID = environ['ONE_SIGNAL_APP_ID']
ONE_SIGNAL_API_KEY = environ['ONE_SIGNAL_API_KEY']


@dataclass
class SendRequest(JsonSchemaMixin):
    message: str


header = {"Content-Type": "application/json; charset=utf-8",
          "Authorization": f"Basic {ONE_SIGNAL_API_KEY}"}

PAYLOAD = {"app_id": ONE_SIGNAL_APP_ID,
           "included_segments": ["All"],
           "contents": {"en": "English Message"}}


app = Flask(__name__)


@app.route('/send', methods=['POST'])
def send():
    try:
        data = SendRequest.from_json(request.data)

    except ValidationError as e:
        logger.error(f'{e}')
        return f'{type(e).__name__}:{e}', 400

    payload = deepcopy(PAYLOAD)
    payload['contents']['en'] = data.message

    try:
        requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=dumps(payload))

    except Exception as e:
        logger.error(f'{type(e)}:{e}')

    return 'SENT'


@app.route('/')
def root():
    return render_template('index.html', app_id=ONE_SIGNAL_APP_ID)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
