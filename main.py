from flask import Flask, jsonify, request, send_from_directory

import yt_dlp as youtube_dl

import requests
import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials


from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Isso permite requisições de qualquer origem

ffmpeg_location = "E:/Meus Programas/ffmpeg-2024/bin/ffmpeg.exe"
# Configuração do Spotify
client_id = '01e862af1ef6487493adbe9ddf708b60'
client_secret = '6e8f904f5bf44649907fbaab2bee5819'    
credentials = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
spotify = Spotify(client_credentials_manager=credentials)

# Certifique-se de que a pasta 'musica' exista
music_folder = 'Musica'
if not os.path.exists(music_folder):
    os.makedirs(music_folder)


# Rota para pesquisa de músicas no Spotify
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Parâmetro "query" é obrigatório'}), 400

    try:
        # Faz a busca de faixas no Spotify
        result = spotify.search(q=query, limit=5, type='track', market='BR')
        tracks = result['tracks']['items']
 
        # Mapeia as faixas encontradas para extrair as informações desejadas
        music_info_list = [
            {
                'Id': track['id'],
                'Nome': track['name'],
                'Cantor': ', '.join([artist['name'] for artist in track['artists']]),
                'Imagem': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'Tempo': track['duration_ms'] / 1000  # Converte milissegundos para segundos
            }
            for track in tracks
            if track['duration_ms'] <= 600 * 1000  # Filtra faixas com até 600 segundos (10 minutos)
        ]

        if music_info_list:
            return jsonify(music_info_list)
        else:
            return jsonify({'error': 'Nenhuma música encontrada'}), 404

    except Exception as e:
        print('Problema em [getMusicInfo]:', e)
        return jsonify({'error': 'Erro interno do servidor'}), 500



@app.route('/audio', methods=['GET'])
def audio():
    query = request.args.get('query')
    music_id = request.args.get('id')
    
    if not query:
        return jsonify({'error': 'Parâmetro "query" é obrigatório'}), 400
    if not music_id:
        return jsonify({'error': 'Parâmetro "id" é obrigatório'}), 400

    try:
        # Busca no YouTube usando youtube_dl
        ytdl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': ffmpeg_location,
            'outtmpl': os.path.join(music_folder, f'{music_id}'),
        }

        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            search_url = f"ytsearch:{query}"
            info_dict = ydl.extract_info(search_url, download=True)
            video = info_dict['entries'][0]

        # Construindo a URL do servidor para retornar
        server_url = request.host_url
        audio_url = f"{server_url}{music_folder}/{music_id}.mp3"

        return jsonify({'url': audio_url})

    except Exception as e:
        print('Problema em [youtubemusic]:', e)
        return jsonify({'error': 'Erro ao processar áudio'}), 500


@app.route('/Musica/<path:filename>', methods=['GET'])
def serve_music(filename):
    return send_from_directory(music_folder, filename)


# Rota principal
@app.route('/')
def home():
    return 'Hello World!'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
