
from app.dependencias import *
from app.search_api import search_bp
from app.audio_api import extract_audio_bp
from app.status_update_api import update_view_bp, top_songs_bp
from app.banco_ms import init_db



app = Flask(__name__)
CORS(app)

app.static_folder = 'static'
app.register_blueprint(search_bp)
app.register_blueprint(update_view_bp)
app.register_blueprint(extract_audio_bp)
app.register_blueprint(top_songs_bp)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route('/')
def home():
    try:
        init_db(1)
        return "Server está Online: OneSong Server!"
        
    except Exception as e:
        return f"vServer está Offiline: {str(e)}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)