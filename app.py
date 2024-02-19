import pandas as pd
import numpy as np
import os

from utils.api_calls import get_top_features
from utils.clustering import process_dataframe, find_closest_album,create_and_fill_playlist,process_bob,get_recommended_songs

import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from dash import Dash, html, dcc, callback, Output, Input,State

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

feature_columns = [
    'danceability_mean',
    'energy_mean',
    'key_mode',
    'loudness_mean',
    'mode_mode',
    'speechiness_mean',
    'acousticness_mean',
    'instrumentalness_mean',
    'liveness_mean',
    'valence_mean',
    'tempo_mean',
    'time_signature_mode'
]
cat_col = ['mode', 'key', 'time_signature']
con_col = ['danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']

raw_bob = pd.read_csv('data/bob_features.csv')
bob_album_ag = process_bob(raw_bob, cat_col, con_col)

user_raw = pd.read_csv('data/example_user_features.csv')

scope = "user-library-read user-top-read playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id = SPOTIPY_CLIENT_ID,client_secret=SPOTIPY_CLIENT_SECRET ,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,scope=scope))

app = Dash(__name__)

user = sp.current_user()

app.layout = html.Div([
    html.Div([
    html.H1('Find Your Bob'),
    html.P('Discover your personal slice of Bob'),
    ],style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
    html.Div([
    html.H2('Find Your Bob Album'),
    html.P("Find the album in Bob's discography that best matches your musical preferences."),
    ],style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
    html.Div([
        html.Button('Find your Bob Album', id='album-button', n_clicks=0)
    ], style={'textAlign': 'center'}),
    html.Div(id='album-recommendation'),
    html.Div([
    html.H2('Make your Bob playlist'),
    html.P("Get a playlist of Bob songs customized to your listening profile."),
    ],style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
    html.Div([
        html.Button('Create Playlist', id='playlist-button', n_clicks=0)
    ], style={'textAlign': 'center'}),
    html.Div(id='playlist-creation')
])

@app.callback(
    Output('album-recommendation', 'children'),
    [Input('album-button', 'n_clicks')]
)
def recommend_album(n_clicks):
    closest_album = find_closest_album(user_raw, bob_album_ag, feature_columns)
    if n_clicks > 0:
        return f"Your Bob match is: {closest_album}"
    
@app.callback(
    Output('playlist-creation', 'children'),
    [Input('playlist-button', 'n_clicks')]
)
def create_playlist(n_clicks):
    if n_clicks > 0:
        averages = process_dataframe(user_raw, cat_col)
        user_info = get_recommended_songs(raw_bob, averages)
        create_and_fill_playlist(user_info, user)

if __name__ == '__main__':
    app.run_server(debug=True)