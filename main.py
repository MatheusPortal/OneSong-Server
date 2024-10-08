from flask import Flask, jsonify, request, send_from_directory
import yt_dlp as youtube_dl
import requests
import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from flask_cors import CORS
import subprocess
import platform
import shutil
import zipfile
import glob


app = Flask(__name__)
CORS(app)  # Isso permite requisições de qualquer origem


def install_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("FFmpeg já está instalado.")
    except FileNotFoundError:
        system_platform = platform.system()
        if system_platform == "Windows":
            print("FFmpeg não encontrado. Instalando no Windows...")
            url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
            ffmpeg_zip = "ffmpeg.zip"

            # Baixar o arquivo zip do FFmpeg
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(ffmpeg_zip, 'wb') as file:
                    shutil.copyfileobj(response.raw, file)

            # Extrair o arquivo zip
            with zipfile.ZipFile(ffmpeg_zip, 'r') as zip_ref:
                zip_ref.extractall("ffmpeg")

            # Encontrar a pasta binária do FFmpeg após a extração
            extracted_folder = glob.glob("ffmpeg/ffmpeg-*-essentials_build/bin")[0]

            # Mover binários para o diretório de trabalho atual
            for file in os.listdir(extracted_folder):
                shutil.move(os.path.join(extracted_folder, file), os.getcwd())

            # Deletar o arquivo zip após a extração
            os.remove(ffmpeg_zip)

            # Remover a pasta temporária usada para extração
            shutil.rmtree("ffmpeg")

            print("FFmpeg instalado com sucesso no Windows.")
        elif system_platform == "Linux":
            print("FFmpeg não encontrado. Instalando no Linux...")
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=True)
            print("FFmpeg instalado com sucesso no Linux.")
        else:
            raise Exception("Sistema operacional não suportado para instalação automática do FFmpeg.")

install_ffmpeg()


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
            'outtmpl': os.path.join(music_folder, f'{music_id}'),
        }

        with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
            search_url = f"ytsearch:{query}"
            info_dict = ydl.extract_info(search_url, download=True)

        # Construindo a URL do servidor para retornar
        server_url = request.host_url.replace("http://", "https://")
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
