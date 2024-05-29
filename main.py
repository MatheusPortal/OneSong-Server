import time
from flask import Flask, request, jsonify
import yt_dlp
from difflib import SequenceMatcher
import os
from pytube import YouTube
from moviepy.editor import *
from flask import request, jsonify
from datetime import datetime, timedelta
from unidecode import unidecode
import sqlite3
import os
from youtube_dl import YoutubeDL
import json
import re
import time
import speech_recognition as sr

from cryptography.fernet import Fernet
import os
import unicodedata
from flask_cors import CORS



app = Flask(__name__)
CORS(app, origins='*')

app.static_folder = 'static'


DB_FILE = "static/song_cache.db"


def init_db():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id TEXT PRIMARY KEY,
                nome TEXT,
                url TEXT,
                imagem TEXT,
                tempo INTEGER,
                view INTEGER DEFAULT 0,
                like INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print("Erro ao inicializar o banco de dados:", e)


def remover_caracteres_especiais(s, op=0):
    tex = ''
    text_re = f'{s}'.replace('-', '').split()

    # guarda no banco
    if op != 0:
        new_s = re.sub(r'\[[^\]]*\]', '', s)
        new_s = ''.join(c for c in unicodedata.normalize('NFD', s)
                        if unicodedata.category(c) != 'Mn')
        new_s = re.sub(r'[^\w\s]', '', new_s.upper())
        new_s = re.sub(r'[^\w\s()]', '', new_s.upper())

        new_s = new_s.split()

        for i, p in enumerate(new_s):
            if p.replace(
                    ' ', ''
            ) not in 'LYRICSMUSICAOFICIALOFFICIALLETRALIVERADIOVIDEOAOVIVOCLIPEAUDIO' and '()' not in text_re[
                    i]:
                tex += f'{text_re[i]} '.capitalize()

    # comparar musica
    else:
        # Remove acentos
        s = ''.join(c for c in unicodedata.normalize('NFD', s)
                    if unicodedata.category(c) != 'Mn')
        s = re.sub(r'[^\w\s]', '', s.lower())

        # Define a expressão regular para encontrar caracteres especiais
        padrao = r'[^a-zA-Z0-9\s]'

        # Substitui os caracteres especiais por uma string vazia
        tex = re.sub(padrao, '', s)
        tex = f'{tex}'.lower()

    return tex


def buscar_musicas(song_query):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()

        # Criar a tabela se não existir
        c.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id TEXT PRIMARY KEY,
                nome TEXT,
                url TEXT,
                imagem TEXT,
                tempo INTEGER,
                view INTEGER DEFAULT 0,
                like INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

        # Buscar músicas semelhantes no banco de dados
        c.execute("SELECT * FROM songs")
        similar_results = list()

        rows = c.fetchall()

        for item in rows:
            if remover_caracteres_especiais(f'{song_query}'.replace(' ', '')) in remover_caracteres_especiais(F'{item[1]}'.replace(' ', '')):
                similar_results.append(item)


        # Se houver resultados semelhantes no banco de dados, retorná-los
        if similar_results:
            print("Retornando resultados semelhantes do cache.")
            results_banco = list()
            for dados in similar_results:
                tabela = {
                    'id': dados[0],
                    'nome': dados[1],
                    'url': dados[2],
                    'imagem': dados[3],
                    'tempo': dados[4],
                    'views': dados[5],
                    'like': dados[6]
                }
                results_banco.append(tabela)

            return results_banco

        # Se não houver resultados semelhantes no banco de dados, buscar no YouTube
        ydl_opts_info = {
            'quiet': True,
            'skip_download': True,
            'age_limit': 18,
            'format': 'bestvideo[ext!=mhtml]',
            'extractor_args': {
                'ytsearch5': {
                    'download': False,
                    'noplaylist': True,
                    'live': False
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            try:
                info_dict = ydl.extract_info(f"ytsearch5:Music {song_query}", download=False)
                song_options = info_dict.get("entries", [])
            except Exception as e:
                print(f"Erro ao consultar o YouTube com yt_dlp: {e}")
                song_options = []

        # Extrair os detalhes das músicas
        song_details = []
        for song in song_options:
            detail = obter_detalhes(song)
            if detail:
                song_details.append(detail)
            else:
                break

        # Inserir os detalhes das músicas na tabela
        for detail in song_details:
            c.execute("INSERT OR IGNORE INTO songs (id, nome, url, imagem, tempo) VALUES (?, ?, ?, ?, ?)", 
                      (detail['id'], detail['nome'], detail['url'], detail['imagem'], detail['tempo']))

        # Confirmar a transação e fechar a conexão com o banco de dados
        conn.commit()
        conn.close()

        return song_details

    except sqlite3.Error as e:
        print("Erro de SQLite:", e)
        return []


def extrair_id_do_video(url):
    # Expressão regular para extrair o ID do vídeo
    pattern = r"(?<=watch\?v=)[a-zA-Z0-9_-]+"
    match = re.search(pattern, url)
    if match:
        return match.group(0)
    else:
        return None


def identificar_genero(titulo):
    # Dicionário de padrões para identificar gêneros
    generos = {
        'pop': ['pop', 'músicas pop'],
        'rock': ['rock', 'rock and roll'],
        'mpb': ['mpb', 'música popular brasileira'],
        'trap': ['trap'],
        'funk': ['funk'],
        'eletronica': ['eletrônica', 'edm', 'música eletrônica'],
        'sertanejo': ['sertanejo'],
        'latina': ['latina', 'músicas latinas'],
        'para você': ['para você', 'for you'],
        'jogos': ['jogos', 'trilha sonora de jogos'],
        'classica': ['clássica', 'música clássica'],
        'filmes': ['filmes', 'trilha sonora de filmes'],
        'pagode': ['pagode'],
    }

    # Converte o título para minúsculas para uma comparação case-insensitive
    titulo_lower = titulo.lower()

    # Verifica se algum padrão está presente no título
    for genero, padroes in generos.items():
        for padrao in padroes:
            if padrao in titulo_lower:
                return genero

    return 'desconhecido'  # Caso não encontre correspondência


def obter_detalhes(song):
    song_query = song.get("webpage_url", "")
    duration_in_minutes = song.get('duration', 0) // 60

    if duration_in_minutes <= 10 and 'thumbnail' in song and song_query and duration_in_minutes >= 2:
        genero = identificar_genero(remover_caracteres_especiais(song.get('title', '')))
        print(genero)
        song_detail = {
            'id': extrair_id_do_video(song_query),
            'nome': remover_caracteres_especiais(song.get('title', ''), 1),
            'url': song_query,
            'imagem': song.get('thumbnail', ''),
            'tempo': song.get('duration', 0),
            'views': 0,
            'like': 0,
            'genero': genero
        }

        return song_detail
    else:
        print(f'Ignorando vídeo: {song_query}')
        return None


def extract_audio_youtube_video(youtube_url, output_filename):
    try:
        output_filename = f'static/Audios/{output_filename}.mp4'

        if os.path.isfile(output_filename):

            # Se o arquivo existir, retorne o URL diretamente
            return output_filename

        # Tentar inicializar o objeto YouTube
        try:
            yt = YouTube(youtube_url)
        except Exception as e:
            print("Erro ao inicializar o objeto YouTube:", e)
            return None

        # Verificar se o vídeo está disponível
        if not yt.streams.filter(only_audio=True).first():
            raise ValueError(f'O vídeo em {youtube_url} não está disponível ou não contém áudio')

        video = yt.streams.filter(only_audio=True).first()
        video.download(filename=output_filename)

        # Aguardar até que o download seja concluído
        while not os.path.exists(output_filename):
            time.sleep(1)

        return output_filename

    except ValueError as ve:
        print("Erro ao extrair áudio do vídeo:", ve)
        return None

    except Exception as e:
        print("Erro ao extrair áudio do vídeo:", e)
        return None



@app.route('/extract_audio', methods=['POST'])
def extract_audio():
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url')
        nome_video = data.get('id_url')
        nome = str(nome_video)

        nome = remover_caracteres_especiais(nome)

        output_filename = data.get('output_filename', f"{nome.replace(' ', '')}")

        # Caso contrário, extraia o áudio do vídeo do YouTube
        audio_filepath = extract_audio_youtube_video(youtube_url, output_filename)


        # Verifique se a extração foi bem-sucedida e retorne o caminho do arquivo de áudio
        if audio_filepath:
            audio_filepath = f'https://a503d1d5-3be1-4323-ab14-eed957710dca-00-3rn8haxlu4pvq.worf.replit.dev:5000/{audio_filepath}'
            return jsonify(audio_url=audio_filepath)
        else:
            return jsonify(error="")

    except Exception as e:
        app.logger.error(f'Error extracting audio: {str(e)}')
        return jsonify(error=""), 500



@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()

        # Verificar se os dados de entrada são válidos
        if data is None or 'query' not in data or not isinstance(data['query'], str) or not data['query'].strip():
            return jsonify({}), 400

        query = data['query']
        song_details = buscar_musicas(remover_caracteres_especiais(query))

        return jsonify(song_details)

    except Exception as e:
        app.logger.error(f'Error processing search: {str(e)}')
        return jsonify({}), 500



@app.route('/update-view', methods=['POST'])
def update_view():
    try:
        init_db()

        data = request.get_json()
        result_id = data['id']

        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()

        # Busca o resultado no banco de dados
        c.execute("SELECT * FROM songs WHERE id = ?", (result_id,))
        result = c.fetchone()

        if result:
            # Incrementa o contador de visualizações
            view_count = result[5] + 1
            # Atualiza o banco de dados com o novo contador de visualizações
            c.execute("UPDATE songs SET view = ? WHERE id = ?", (view_count, result_id))
            conn.commit()
            conn.close()
            return jsonify({'message': 'View count updated successfully'}), 200
        else:
            conn.close()
            return jsonify({'message': 'Result not found'}), 404
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500



@app.route('/top-songs', methods=['GET'])
def top_songs():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()

        # Seleciona os 10 registros com mais visualizações
        c.execute("SELECT id, nome, url, imagem, tempo, view, like FROM songs ORDER BY view DESC LIMIT 10")
        rows = c.fetchall()

        # Formata os registros no mesmo formato dos resultados da pesquisa do YouTube
        top_songs = []
        for row in rows:
            top_songs.append({
                'id': row[0],
                'nome': row[1],
                'url': row[2],
                'imagem': row[3],
                'tempo': row[4],
                'views': row[5],
                'like': row[6]
            })

        conn.close()
        return jsonify(top_songs), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500



@app.route('/')
def home():
    return "Server está Online: OneSong Server!"


@app.route('/ping')
def ping():
    print("Acesso ao /ping")
    return "pong", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)