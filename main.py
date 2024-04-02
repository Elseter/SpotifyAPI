import urllib.parse

import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = "http://localhost:5000/callback"
Auth_URL = "https://accounts.spotify.com/authroize/"
Token_URL = "https://accounts.spotify.com/api/token/"
Base_URL = "https://api.spotify.com/v1/"

app = Flask(__name__)
app.secret_key = "1234"

currently_playing = None


@app.route("/")
def index():
    return "Welcome to my Spotify Client <a href='/login'>Login with spotify</a>"


@app.route("/login")
def login():
    scopes = 'user-read-email user-library-read playlist-read-private streaming user-read-playback-state user-modify-playback-state user-read-currently-playing'

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scopes,
        'redirect_uri': redirect_uri,
        'show_dialog': True
    }

    auth_url = f"{Auth_URL}?{urllib.parse.urlencode(params)}"
    print(auth_url)

    return redirect(
        "https://accounts.spotify.com/en/authorize/?client_id=0722981b2f2047e6bffb6ad65f08e8f9&response_type=code&redirect_uri=http://localhost:5000/callback&scope=user-read-email%20user-library-read%20playlist-read-private%20streaming%20user-read-playback-state%20user-modify-playback-state%20user-read-currently-playing&show_dialog=true")


@app.route("/callback")
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(Token_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_in'] = datetime.now().timestamp() + token_info['expires_in']
        print(token_info['expires_in'])
        return redirect('/home')


@app.route("/playlist")
def get_playlist():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(f"{Base_URL}me/playlists", headers=headers)
    playlist = response.json()

    return redirect('/home')


@app.route("/play")
def play():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.put(f"{Base_URL}me/player/play", headers=headers)
    return redirect('/home')


@app.route("/pause")
def pause():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.put(f"{Base_URL}me/player/pause", headers=headers)
    return redirect('/home')


@app.route("/next")
def next_song():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.post(f"{Base_URL}me/player/next", headers=headers)
    return redirect('/home')


@app.route("/previous")
def previous_song():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.post(f"{Base_URL}me/player/previous", headers=headers)
    return redirect('/home')


@app.route("/refresh_token")
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(Token_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_in'] = datetime.now().timestamp() + token_info['expires_in']

    return redirect('/playlist')


@app.route("/current_song")
def get_current():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(f"{Base_URL}me/player/currently-playing", headers=headers)
    current = response.json()

    artist = current['item']['artists'][0]['name']
    song = current['item']['name']
    album_cover = current['item']['album']['images'][0]['url']

    # Display the song, artist and album cover on webpage
    return jsonify({"artist": artist, "song": song, "album_cover": album_cover})


@app.route("/home")
def home():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_in']:
        return redirect('/refresh_token')

    # Get Current Song info
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(f"{Base_URL}me/player/currently-playing", headers=headers)
    current = response.json()

    artist = current['item']['artists'][0]['name']
    song = current['item']['name']
    album_cover = current['item']['album']['images'][0]['url']

    if artist is None:
        artist = "No artist"
        song = "No song"
        album_cover = "https://i.pinimg.com/originals/3c/9c/5e/3c9c5e5f4b6e2a2a3d4d6b7a6c3d6e5e.jpg"

    # Get queue of songs
    response = requests.get(f"{Base_URL}me/player/queue", headers=headers)
    queue = response.json()

    upcoming = []

    for queued_songs in queue["queue"]:
        upcoming.append(queued_songs["name"])

    print(upcoming)

    return render_template('home.html', artist=artist, song=song, album_cover=album_cover, queue=upcoming)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
