from main import *
from app.search_api import remover_caracteres_especiais



def normalize_audio(input_filepath):
    # Carrega o áudio usando pydub
    audio = AudioSegment.from_file(input_filepath)

    # Normaliza o volume para -1.5 dBFS
    change_in_dBFS = -1.5 - audio.max_dBFS
    normalized_audio = audio.apply_gain(change_in_dBFS)

    # Exporta o áudio normalizado em MP3
    normalized_audio.export(input_filepath, format='mp3')


def extract_audio_youtube_video(youtube_url, output_filename):
    try:
        output_dir = 'static/Audios'
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f'{output_filename}.mp3')

        if os.path.isfile(output_filepath):
            # Se o arquivo existir, retorne o caminho diretamente
            return output_filepath

        # Opções para yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, f'{output_filename}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Normaliza o áudio extraído
        normalize_audio(output_filepath)

        return output_filepath

    except yt_dlp.utils.DownloadError as e:
        print("Erro ao extrair áudio do vídeo:", e)
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

        # Extraia o áudio do vídeo do YouTube
        audio_filepath = extract_audio_youtube_video(youtube_url, output_filename)

        # Verifique se a extração foi bem-sucedida e retorne o caminho do arquivo de áudio
        if audio_filepath:
            audio_url = f'https://a503d1d5-3be1-4323-ab14-eed957710dca-00-3rn8haxlu4pvq.worf.replit.dev:5000/{audio_filepath}'
            return jsonify(audio_url=audio_url)
        else:
            return jsonify(error="Erro ao extrair o áudio do vídeo.")

    except Exception as e:
        app.logger.error(f'Error extracting audio: {str(e)}')
        return jsonify(error="Erro interno no servidor."), 500

