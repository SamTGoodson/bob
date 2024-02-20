import pandas as pd
import numpy as np
import os

from utils.api_calls import get_top_features
from utils.clustering import process_dataframe, find_closest_album,create_and_fill_playlist,process_bob,get_recommended_songs
from data.static import album_titles,cat_col,con_col,feature_columns

import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from dash import Dash, html, dcc, callback, Output, Input,State
import dash_bootstrap_components as dbc

manual_catagorical_cols = ['mode', 'key', 'time_signature']

raw_bob = pd.read_csv('data/bob_features.csv')
bob_album_ag = process_bob(raw_bob, cat_col, con_col)

#example = pd.read_csv('data/example_user_features.csv')
bob_with_images = pd.read_csv('data/bob_with_images.csv')

scope = "user-library-read user-top-read playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

user_raw = get_top_features(sp)
averages = process_dataframe(user_raw, manual_catagorical_cols)

app = Dash(__name__,external_stylesheets=[dbc.themes.FLATLY])
server = app.server

user = sp.current_user()

studio_only = bob_with_images[bob_with_images['album_name'].isin(album_titles)]

app.layout = html.Div([
    html.Div([
    html.Img(src='https://upload.wikimedia.org/wikipedia/commons/a/a7/Bob_Dylan_1978.jpg', style={'height': '300px', 'width': '300px', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'}),
    ]),
    html.Div([
    html.H1('Find Your Bob'),
    html.P('The discography of our greatest living songwriter can be large and overwhelming, where is a newcomer to dive into the great river of Bob? Maybe you know of Bob’s work from the ‘60s but don’t know where to dive into the other stuff. Here at Find Your Bob, we offer some assistance, log in with your Spotify account and we’ll show you the album that best matches your Spotify listening history, as well as make you a personalized Bob playlist. '),
    ],style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
    html.Div([
    html.H2('Find Your Bob Album'),
    html.P("Find the album in Bob's discography that best matches your musical preferences. Select whether you’d like to only see studio albums or if you’d like to include bootlegs and live recordings as well. "),
    ],style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
        html.Div([
        dcc.Checklist(
            id='dataset-selector',
            options=[
                {'label': 'Only Studio Albums', 'value': 'ALT'},
            ],
            value=[]
        )
    ], style={'padding': '10px','text-align': 'center'}),
    html.Div([
        html.Button('Find your Bob Album', id='album-button', n_clicks=0)
    ], style={'textAlign': 'center'}),
    html.Div(id='album-recommendation', style={'text-align': 'center'}),
    html.Div([
    html.H2('Make your Bob playlist'),
    html.P("Get a playlist of Bob songs customized to your listening profile."),
    ],style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
    html.Div([
        html.Button('Create Playlist', id='playlist-button', n_clicks=0)
    ], style={'textAlign': 'center'}),
    html.Div(id='playlist-creation',style={'padding': '15px','textAlign': 'center'})
])


@app.callback(
    Output('album-recommendation', 'children'),
    [Input('album-button', 'n_clicks')],
    [State('dataset-selector', 'value')]
)
def recommend_album(n_clicks, dataset_selection):
    if n_clicks > 0:
        averages = process_dataframe(user_raw, manual_catagorical_cols)
        if 'ALT' in dataset_selection:
            closest_album, album_image_url = find_closest_album(averages, studio_only, feature_columns)
        else:
            closest_album, album_image_url = find_closest_album(averages,bob_with_images, feature_columns)
        
        return html.Div([
            html.P(f"Your Bob match is: {closest_album}"),
            html.Img(src=album_image_url, style={'height': '300px', 'width': '300px', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'})
        ])

    
@app.callback(
    Output('playlist-creation', 'children'),
    [Input('playlist-button', 'n_clicks')]
)
def create_playlist(n_clicks):
    if n_clicks > 0:
        try:
            recommended_songs_df = get_recommended_songs(raw_bob,averages)
            print(recommended_songs_df.head())
            create_and_fill_playlist(recommended_songs_df,user)
            return html.Div([
            html.P("Your playlist was successfully created, enjoy your very own slice of Bob."),
            html.Img(src='https://upload.wikimedia.org/wikipedia/commons/3/37/President_Barack_Obama_presents_American_musician_Bob_Dylan_with_a_Medal_of_Freedom.jpg', style={'height': '300px', 'width': '300px', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'}),
        ])
        except Exception as e:
            return "An error occurred while creating the playlist, please text Sam what time this happened."

if __name__ == '__main__':
    app.run_server(debug=True)