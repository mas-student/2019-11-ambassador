#!/usr/bin/python
# -*- coding: utf8 -*-

from os import environ
from contextlib import contextmanager
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from unittest.mock import ANY, Mock, patch

from aiohttp import web
from aiohttp.test_utils import TestClient
from asyncmock import AsyncMock
from dataclasses_jsonschema import JsonSchemaMixin, ValidationError
from pytest import fixture


@dataclass
class SendRequest(JsonSchemaMixin):
    message: str


SMTP_HOST = environ['SMTP_HOST']
SMTP_PORT = environ['SMTP_PORT']
SMTP_USERNAME = environ['SMTP_USERNAME']
SMTP_PASSWORD = environ['SMTP_PASSWORD']
RECEIVERS = environ['RECEIVERS'].split(',')


def init_smtp(source_login, source_password, smtp_host, smtp_port):
    connection = SMTP(host=smtp_host, port=smtp_port)
    connection.starttls()
    connection.login(source_login, source_password)

    return connection


@contextmanager
def smtp(source_login, source_password, smtp_host, smtp_port):
    connection = SMTP(host=smtp_host, port=smtp_port)
    connection.starttls()
    connection.login(source_login, source_password)

    try:
        yield connection

    finally:
        connection.quit()


def init_app():
    app = web.Application()
    app.router.add_post('/send', handler_send)
    return app


async def smtp_send(sender, receiver, message, smtp_connection):
    msg = MIMEMultipart()

    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = F'Automatic sending {message[:3]}'

    msg.attach(MIMEText(message, 'plain'))

    smtp_connection.send_message(msg)

    del msg


async def send(destinations, message, source_login, source_password, smtp_host, smtp_port):
    emails = [email for email, name in destinations]
    names = [name for email, name in destinations]

    with smtp(source_login, source_password, smtp_host, smtp_port) as smtp_connection:
        for name, email in zip(names, emails):
            await smtp_send(sender=source_login, receiver=email, message=message, smtp_connection=smtp_connection)


async def handler_send(request):
    try:
        data = SendRequest.from_json(await request.text())

    except ValidationError as e:
        return web.Response(status=400, text=str(e))

    await send(
        message=data.message,
        source_login=SMTP_USERNAME,
        source_password=SMTP_PASSWORD,
        destinations=[(email, email.split('@')[0].lower()) for email in RECEIVERS],
        smtp_host=SMTP_HOST,
        smtp_port=SMTP_PORT,
    )

    return web.Response(status=200, text='SENT')


app = init_app()


if __name__ == '__main__':
    web.run_app(app)


@fixture()
def client(loop, aiohttp_client):
    app = init_app()
    return loop.run_until_complete(aiohttp_client(app))


async def test_send_incorrect(client):
    assert (await client.post('', json={})).status == 400


async def test_send_correct(client):
    assert (await client.post('', json={'emails': ['user@site.com']})).status == 200


async def test_smtp_send(client):
    with patch('main.smtp_send', new=AsyncMock()) as mocked_smtp_send:
        print(mocked_smtp_send)
        assert (await client.post('', json={'message': 'hello', 'emails': ['user@site.com']})).status == 200
        mocked_smtp_send.assert_called_with(sender=SMTP_USERNAME, receiver='user@site.com', message='hello', smtp_connection=ANY)
