import pandas as pd
import numpy as np
import os

import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

from scipy.spatial import distance

from sklearn.neighbors import NearestNeighbors

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

scope = "user-library-read user-top-read playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id = SPOTIPY_CLIENT_ID,client_secret=SPOTIPY_CLIENT_SECRET ,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,scope=scope))

manual_catagorical_cols = ['mode', 'key', 'time_signature']
feature_columns = ['danceability_mean', 'energy_mean', 'loudness_mean','speechiness_mean',
                    'acousticness_mean', 'instrumentalness_mean','liveness_mean', 'valence_mean',
                      'tempo_mean', 'mode_mode', 'key_mode','time_signature_mode'] 

def process_dataframe(df, manual_categorical_cols=None, unique_value_threshold=10):
    processed_data = {}
    
    df = df.drop(columns=['id'])
    
    if manual_categorical_cols is None:
        manual_categorical_cols = []
    
    for col in df.columns:
        if df[col].nunique() <= unique_value_threshold or col in manual_categorical_cols:

            processed_data[col + '_mode'] = df[col].mode()[0]
        else:

            processed_data[col + '_mean'] = df[col].mean()
    
    
    return processed_data

def find_closest_album(user_raw,album_features, feature_columns):
    max_similarity = -1  
    closest_album = None

    averages_features = [user_raw[col] for col in feature_columns]
    user_features = np.array(averages_features).flatten()

    for index, row in album_features.iterrows():
        album_features = row[feature_columns].tolist()  
        similarity = 1 - distance.cosine(user_features, album_features)  
        if similarity > max_similarity:
            max_similarity = similarity
            closest_album = row['album_name']  

    return closest_album


def get_recommended_songs(songs,user_info):
    X = songs.drop(columns=['id', 'track_name', 'album_name'])
    knn = NearestNeighbors(n_neighbors=30)
    knn.fit(X)
    user_profile = np.array([user_info[feature] for feature in feature_columns]).reshape(1, -1)
    distances, indices = knn.kneighbors(user_profile)
    recommended_songs_df = songs.iloc[indices[0]][['track_name', 'id']]
    return recommended_songs_df


def create_and_fill_playlist(recommended_songs_df,user):
    user_id = user['id']
    playlist = sp.user_playlist_create('stg58661521',"FindYourBob", public=True, collaborative=False, description='Discovering your personal slice of Bob')
    track_ids = recommended_songs_df['id'].tolist()
    sp.user_playlist_add_tracks(user_id, playlist['id'], track_ids, position=None)
    print("Playlist created and filled with recommended songs.")

def process_bob(bob_df, cat_cols, con_cols):

    processed_data = pd.DataFrame()
    
    grouped = bob_df.groupby('album_name')
    
    for col in con_cols:
        if col in bob_df.columns:
            processed_data[col + '_mean'] = grouped[col].mean()
    
    for col in cat_cols:
        if col in bob_df.columns:
            processed_data[col + '_mode'] = grouped[col].apply(lambda x: x.mode()[0] if not x.mode().empty else None)
    
    processed_data = processed_data.reset_index()
    
    return processed_data
