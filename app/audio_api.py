from app.dependencias import *
from app.banco_ms import url_serve


def normalize_audio(input_filepath):
    audio = AudioSegment.from_file(input_filepath)
    change_in_dBFS = -1.5 - audio.max_dBFS
    normalized_audio = audio.apply_gain(change_in_dBFS)
    normalized_audio.export(input_filepath, format='mp3')


def extract_audio_youtube_video(youtube_url, nome_audio, diretorio):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join('static/Audios', f'{nome_audio}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        normalize_audio(diretorio)

        return diretorio

    except Exception as e:
        print(f"Erro ao extrair áudio do vídeo: {e}")
        return None


extract_audio_bp = Blueprint('/extract_audio', __name__)
@extract_audio_bp.route('/extract_audio', methods=['POST'])
def extract_audio():
    # Aqui ira tentar extrair o audio usando a biblioteca do youtube para extração de audio, depois normalizar o volume e renome-lo para o id da url.
    try:
        #Colher dados da API
        dados = request.get_json()
        youtube_url = dados.get('youtube_url')
        nome_audio = str(dados.get('id_url')).replace(' ', '').lower()

        diretorio = 'static/Audios'
        os.makedirs(diretorio, exist_ok=True)
        diretorio_saida = os.path.join(diretorio, f'{nome_audio}.mp3')

        if os.path.isfile(diretorio_saida):
            return jsonify(audio_url=f'{url_serve}{diretorio_saida}')

        # Extração assíncrona
        with ThreadPoolExecutor() as executor:

            #extração de audio aqui
            audio = executor.submit(extract_audio_youtube_video, youtube_url, nome_audio, diretorio_saida)
            url_audio = audio.result()

            if url_audio:
                audio_url = f'{url_serve}{url_audio}'
                return jsonify(audio_url=audio_url)

            else:
                # Retorne para API um erro de extração de audio.
                return jsonify(error="ErroAD02"), 500

    except Exception as e:
        # Retorne para API um erro de tentativa na extração do audio.
        return jsonify(error="ErroAD01"), 500

