from __future__ import absolute_import

import json
import os
from urlparse import urlparse

from flask import Flask, render_template, request, redirect, session
from flask_sslify import SSLify
from rauth import OAuth2Service
import requests

import logging

app = Flask(__name__, static_folder='static', static_url_path='')
app.requests_session = requests.Session()
app.secret_key = os.urandom(24)

sslify = SSLify(app)

logging.basicConfig(
    format="%(levelname)s: %(asctime)s %(message)s",
    filename="debug.log",
    level=logging.DEBUG,
)

with open('config.json') as f:
    config = json.load(f)


def generate_oauth_service():
    """Prepare the OAuth2Service that is used to make requests later."""
    return OAuth2Service(
        #client_id=os.environ.get('UBER_CLIENT_ID'),
        #client_secret=os.environ.get('UBER_CLIENT_SECRET'),
        name=config.get('name'),
        authorize_url=config.get('authorize_url'),
        access_token_url=config.get('access_token_url'),
        base_url=config.get('base_url'),
    )


def generate_ride_headers(token):
    """Generate the header object that is used to make api requests."""
    return {
        'Authorization': 'bearer %s' % token,
        'Content-Type': 'application/json',
    }


@app.route('/health', methods=['GET'])
def health():
    """Check the status of this application."""
    return ';-)'


@app.route('/', methods=['GET'])
def signup():
    """The first step in the three-legged OAuth handshake.

    You should navigate here first. It will redirect to login.uber.com.
    """
    params = {
        'response_type': 'token',
        'client_id' : 'YTliMWNlYTUtYmRmYy00OTA1LWE1Y2YtMjdiMjljNGY4OTZj',
        #'redirect_uri': get_redirect_uri(request),
        'redirect_uri': 'http://localhost/submit&scope=profile%20booking&state=state123'
        #'scopes': ','.join(config.get('scopes')),
    }
    url = "http://sandbox-t.olacabs.com/oauth2/authorize?response_type=token&client_id=YTliMWNlYTUtYmRmYy00OTA1LWE1Y2YtMjdiMjljNGY4OTZj&redirect_uri=http://localhost/team56&scope=profile%20booking&state=state123"
    return redirect(url)


@app.route('/team56', methods=['GET'])
def submit():
    """The other two steps in the three-legged Oauth handshake.

    Your redirect uri will redirect you here, where you will exchange
    a code that can be used to obtain an access token for the logged-in use.
    """
    # params = {
    #     'redirect_uri': get_redirect_uri(request),
    #     'code': request.args.get('code'),
    #     'grant_type': 'authorization_code'
    # }
    # response = app.requests_session.post(
    #     config.get('access_token_url'),
    #     auth=(
    #         os.environ.get('UBER_CLIENT_ID'),
    #         os.environ.get('UBER_CLIENT_SECRET')
    #     ),
    #     data=params,
    # )
    # session['access_token'] = response.json().get('access_token')

    return render_template(
        'debug.html',
        #token=response.json().get(request)
        token=request.url
    )

@app.route('/book', methods=['GET'])
def book():
    url = "http://sandbox-t.olacabs.com/v1/bookings/create"
    logging.info(session.get('access_token'))
    params = {
        'pickup_lat': request.args['myLat'],
        'pickup_lng': request.args['myLong'],
        'pickup_mode':"NOW",
        'category': request.args['category']
    }
    headers={
        'X-APP-TOKEN': config.get('x_app_token'),
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % session.get('access_token'),
    }
    response = app.requests_session.get(
        url,
        headers=headers,
        params=params,
    )
    return response.text

@app.route('/cancel', methods=['GET'])
def cancel():
    url = "http://sandbox-t.olacabs.com/v1/bookings/cancel"
    params = {
        'crn': request.args['crn']
    }
    headers={
        'X-APP-TOKEN': config.get('x_app_token'),
        'Authorization': 'Bearer %s' % session.get('access_token')
    }
    response = app.requests_session.get(
        url,
        headers=headers,
        params=params,
    )
    return response.text

@app.route('/map', methods=['GET'])
def map():
    return render_template(
        'map.html'
    )

@app.route('/track', methods=['GET'])
def track():
    url = "http://sandbox-t.olacabs.com/v1/bookings/track_ride"

    headers={
        'X-APP-TOKEN': config.get('x_app_token'),
        'Authorization': 'Bearer %s' % session.get('access_token')
    }
    response = app.requests_session.get(
        url,
        headers=headers
    )
    return response.text

@app.route('/is_logged_in', methods=['GET'])
def logged_in():
    if 'access_token' not in session:
        return "false"
    else:
        return "true"

@app.route('/save_token', methods=['POST'])
def save_token():
    post_json=request.get_json(force=True)
    logging.info("in save token, token : "+ post_json['token'])
    session['access_token'] =post_json['token']
    logging.info("after assigning to sesion, token :"+session.get('access_token'))
    return "successful"
    # return render_template(
    #     'debug2.html',
    #     #token=response.json().get(request)
    #     token=session['access_token']
    # )


@app.route('/demo', methods=['GET'])
def demo():
    """Demo.html is a template that calls the other routes in this example."""
    return render_template('demo.html', token=session.get('access_token'))


@app.route('/products', methods=['POST'])
def products():
    """Example call to the products endpoint.

    Returns all the products currently available in San Francisco.
    """
    post_json=request.get_json(force=True)
    category=request.args['category']
    url = config.get('base_ola_url') + 'products'
    params = {
        'pickup_lat': post_json['start_latitude'],
        'pickup_lng': post_json['start_longitude'],
        'drop_lat': post_json['end_latitude'],
        'drop_lng': post_json['end_longitude'],
        'category': category
    }

    response = app.requests_session.get(
        url,
        #headers=generate_ride_headers(session.get('access_token')),
        headers=generate_ola_headers(),
        params=params,
    )

    if response.status_code != 200:
        return 'There was an error', response.status_code
    # return render_template(
    #     'results.html',
    #     endpoint='products',
    #     data=response.text,
    # )
    return response.text;


@app.route('/time', methods=['GET'])
def time():
    """Example call to the time estimates endpoint.

    Returns the time estimates from the given lat/lng given below.
    """
    url = config.get('base_ola_url') + 'estimates/time'
    params = {
        'start_latitude': config.get('start_latitude'),
        'start_longitude': config.get('start_longitude'),
    }

    response = app.requests_session.get(
        url,
        headers=generate_ride_headers(session.get('access_token')),
        params=params,
    )

    if response.status_code != 200:
        return 'There was an error', response.status_code
    return render_template(
        'results.html',
        endpoint='time',
        data=response.text,
    )


@app.route('/price', methods=['GET'])
def price():
    """Example call to the price estimates endpoint.

    Returns the time estimates from the given lat/lng given below.
    """
    url = config.get('base_ola_url') + 'estimates/price'
    params = {
        'start_latitude': config.get('start_latitude'),
        'start_longitude': config.get('start_longitude'),
        'end_latitude': config.get('end_latitude'),
        'end_longitude': config.get('end_longitude'),
    }

    response = app.requests_session.get(
        url,
        headers=generate_ride_headers(session.get('access_token')),
        params=params,
    )

    if response.status_code != 200:
        return 'There was an error', response.status_code
    return render_template(
        'results.html',
        endpoint='price',
        data=response.text,
    )


@app.route('/history', methods=['GET'])
def history():
    """Return the last 5 trips made by the logged in user."""
    url = config.get('base_ola_url_v1_1') + 'history'
    params = {
        'offset': 0,
        'limit': 5,
    }

    response = app.requests_session.get(
        url,
        headers=generate_ride_headers(session.get('access_token')),
        params=params,
    )

    if response.status_code != 200:
        return 'There was an error', response.status_code
    return render_template(
        'results.html',
        endpoint='history',
        data=response.text,
    )


@app.route('/me', methods=['GET'])
def me():
    """Return user information including name, picture and email."""
    url = config.get('base_ola_url') + 'me'
    response = app.requests_session.get(
        url,
        headers=generate_ride_headers(session.get('access_token')),
    )

    if response.status_code != 200:
        return 'There was an error', response.status_code
    return render_template(
        'results.html',
        endpoint='me',
        data=response.text,
    )

def generate_ola_headers():
    return {
        'X-APP-TOKEN': config.get('x_app_token'),
        'Content-Type': 'application/json',
    }

def get_redirect_uri(request):
    """Return OAuth redirect URI."""
    parsed_url = urlparse(request.url)
    if parsed_url.hostname == 'localhost':
        return 'http://{hostname}:{port}/submit'.format(
            hostname=parsed_url.hostname, port=parsed_url.port
        )
    return 'https://{hostname}/submit'.format(hostname=parsed_url.hostname)

if __name__ == '__main__':
    app.debug = os.environ.get('FLASK_DEBUG', True)
    app.run(port=80)
