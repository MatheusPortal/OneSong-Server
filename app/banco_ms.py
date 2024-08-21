from app.dependencias import *

url_serve = "https://7f3ea8fc-7071-42f8-8531-5d92e5158765-00-6sz7p07ke435.janeway.replit.dev:5000/"

# Configurações
DB_FILE = "static/song_cache.db"


def init_db(opc=1):
    try:
        if opc == 1:
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
                    like INTEGER DEFAULT 0,
                    genero TEXT,
                    letra TEXT
                )
            ''')
            conn.commit()
            conn.close()
        
    except sqlite3.Error as e:
        print("Erro ao inicializar o banco de dados:", e)   
