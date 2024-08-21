from app.dependencias import *
from app.banco_ms import init_db, DB_FILE


update_view_bp = Blueprint('update-view', __name__)
top_songs_bp = Blueprint('top-songs', __name__)


def top_songs_async():
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()

        # Seleciona os 10 registros com mais visualizações
        c.execute("SELECT id, nome, url, imagem, tempo, view, like, genero, letra FROM songs ORDER BY view DESC LIMIT 10")
        rows = c.fetchall()

        # Formata os registros no mesmo formato dos resultados da pesquisa do YouTube
        top_songs = [
            {'id': row[0], 'nome': row[1], 'url': row[2], 'imagem': row[3], 'tempo': row[4], 'views': row[5], 'like': row[6], 'genero': row[7], 'letra': row[8]}
            for row in rows if row[5] > 0
        ]
        return top_songs
        
    except Exception as e:
        return []
    

@update_view_bp.route('/update-view', methods=['POST'])
def update_view():
    try:
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
    

@top_songs_bp.route('/top-songs', methods=['GET'])
def top_songs():
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(top_songs_async)
            top_songs = future.result()

        return jsonify(top_songs), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({}), 500
