
from app.dependencias import *
from app.banco_ms import url_serve, init_db, DB_FILE

palavras_para_remover = ['oficial', 'live', 'ao vivo', 'clipe', 'hd', 'audio', 'songs', 'mix', 'mixtape', 'mixes', 'lyric', 'video', 'official', 'music', 'dvd', 'cd', '4k', 'lyrics', 'audío']

search_bp = Blueprint('search', __name__)

ydl_opts_info = {
            'quiet': True,
            'skip_download': True,
            'age_limit': 18,
            'format': 'best',
            'noplaylist': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash'],
                }
            }
        }


def buscar_musicas(song_query):
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        c = conn.cursor()

        # Buscar músicas semelhantes no banco de dados
        c.execute("SELECT * FROM songs")
        similar_results = list()
        rows = c.fetchall()

        for item in rows:
            if remover_caracteres_especiais(f'{song_query}'.replace(' ', '')) in remover_caracteres_especiais(F'{item[1]}'.replace(' ', '')):
                similar_results.append(item)


        # Se houver resultados semelhantes no banco de dados, retorná-los
        if similar_results:
            results_banco = list()
            for dados in similar_results:
                tabela = {
                    'id': dados[0],
                    'nome': dados[1],
                    'url': dados[2],
                    'imagem': dados[3],
                    'tempo': dados[4],
                    'views': dados[5],
                    'like': dados[6],
                    'genero': dados[7],
                    'letra': dados[8]
                }
                results_banco.append(tabela)

            conn.commit()
            conn.close()
            return results_banco

        # Se não houver resultados semelhantes no banco de dados, buscar no YouTube
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            try:
                info_dict = ydl.extract_info(f"ytsearch5:{song_query}", download=False)
                song_options = info_dict.get("entries", [])
            except Exception as e:
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
            c.execute("INSERT OR IGNORE INTO songs (id, nome, url, imagem, tempo, genero, letra) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (detail['id'], detail['nome'], detail['url'], detail['imagem'], detail['tempo'], detail['genero'], detail['letra']))

        # Confirmar a transação e fechar a conexão com o banco de dados
        conn.commit()
        conn.close()

        return song_details

    except sqlite3.Error as e:
        return []


def remover_caracteres_especiais(txt_bruto, opc=0):
    txt_limpo = ''

    txt_bruto = emoji.replace_emoji(txt_bruto, replace='')

    # guarda no banco
    if opc != 0:
        # Remove caracteres especiais e converte para minúsculas
        txt_bruto = re.sub(r'[^\w\s]', '', txt_bruto).lower()
        
        # Remove palavras indesejadas
        for palavra in palavras_para_remover:
            txt_bruto = txt_bruto.replace(palavra, '')

        # Divide o texto em palavras e capitaliza cada palavra
        txt_limpo = ' '.join([palavra.capitalize() for palavra in txt_bruto.split()])

    # comparar musica
    else:
        # Define a expressão regular para encontrar caracteres especiais
        padrao = r'[^a-zA-Z0-9\s]'

        # Remove acentos
        txt_bruto = ''.join(c for c in unicodedata.normalize('NFD', txt_bruto) if unicodedata.category(c) != 'Mn')

        # Substitui os caracteres especiais por uma string vazia
        txt_limpo = re.sub(padrao, '', txt_bruto)
        txt_limpo = f'{txt_limpo}'.lower()

    return txt_limpo


def identificar_genero(titulo):
    # Dicionário de palavras-chave associadas a diferentes gêneros
    generos = {
        'rock': [
            'rock', 'metal', 'hard rock', 'grunge', 'punk', 'alternative', 'Nirvana', 'Metallica', 'Led Zeppelin', 'AC/DC', 'Guns N\' Roses', 
            'Queen', 'Pink Floyd', 'The Rolling Stones', 'U2', 'The Beatles', 'Aerosmith', 'The Who', 'Foo Fighters', 'Red Hot Chili Peppers', 
            'Green Day', 'Pearl Jam', 'Alice in Chains', 'Soundgarden', 'Linkin Park', 'Iron Maiden', 'Black Sabbath', 'Deep Purple', 'KISS', 
            'Bon Jovi', 'Def Leppard', 'Scorpions', 'Van Halen', 'Motörhead', 'Rammstein', 'System of a Down', 'Slipknot', 'Megadeth', 
            'Judas Priest', 'Anthrax', 'Pantera', 'Slayer', 'Rage Against the Machine', 'Muse', 'Radiohead', 'Arctic Monkeys', 'The Strokes', 
            'Oasis', 'Blur', 'The Smashing Pumpkins', 'Lynyrd Skynyrd', 'ZZ Top', 'Dire Straits', 'Rush', 'Yes', 'Genesis', 'Emerson, Lake & Palmer', 
            'King Crimson', 'Jethro Tull', 'Tool', 'Dream Theater', 'Faith No More', 'Nine Inch Nails', 'Marilyn Manson', 'Deftones'
        ],
        'pop': [
            'pop', 'dance', 'electronic', 'top 40', 'chart', 'hits', 'Michael Jackson', 'Madonna', 'Britney Spears', 'Lady Gaga', 'Taylor Swift', 
            'Ariana Grande', 'Justin Bieber', 'Rihanna', 'Beyoncé', 'Katy Perry', 'Bruno Mars', 'Selena Gomez', 'The Weeknd', 'Dua Lipa', 
            'Shawn Mendes', 'Ed Sheeran', 'Billie Eilish', 'Harry Styles', 'Camila Cabello', 'Demi Lovato', 'Christina Aguilera', 'Jennifer Lopez', 
            'Kesha', 'Charlie Puth', 'Sam Smith', 'Maroon 5', 'Justin Timberlake', 'Backstreet Boys', 'NSYNC', 'Jonas Brothers', 'Carly Rae Jepsen', 
            'Ellie Goulding', 'Halsey', 'Lana Del Rey', 'Miley Cyrus', 'Nicki Minaj', 'Cardi B', 'Lil Nas X', 'Jason Derulo', 'Pitbull', 'Shakira', 
            'Tove Lo', 'Adele', 'Lorde', 'Khalid', 'Sia', 'BTS', 'BLACKPINK', 'One Direction', 'Little Mix', 'Fifth Harmony', 'Mabel', 'Anne-Marie'
        ],
        'mpb': [
            'mpb', 'bossa nova', 'samba', 'tropicalia', 'samba-rock', 'Tom Jobim', 'Caetano Veloso', 'Gilberto Gil', 'Chico Buarque', 'Gal Costa', 
            'Elis Regina', 'Maria Bethânia', 'João Gilberto', 'Zé Ramalho', 'Alceu Valença', 'Milton Nascimento', 'Djavan', 'Marisa Monte', 
            'Adoniran Barbosa', 'Martinho da Vila', 'Nara Leão', 'Vinícius de Moraes', 'Toquinho', 'Jorge Ben Jor', 'Gonzaguinha', 'Beth Carvalho', 
            'Clara Nunes', 'Dorival Caymmi', 'Noel Rosa', 'Paulinho da Viola', 'Cartola', 'Nelson Cavaquinho', 'Paulinho Moska', 'Lenine', 
            'Zeca Baleiro', 'Elza Soares', 'Lô Borges', 'Baden Powell', 'Yamandu Costa', 'Hamilton de Holanda', 'Egberto Gismonti', 'Naná Vasconcelos'
        ],
        'trap': [
            'trap', 'hip hop', 'rap', 'urban', 'drill', 'gangsta', 'Eminem', 'Jay-Z', 'Kanye West', 'Dr. Dre', 'Kendrick Lamar', '2Pac', 'Notorious B.I.G.', 
            'Nas', 'Snoop Dogg', 'Lil Wayne', 'Drake', 'Travis Scott', 'Migos', 'Future', 'Cardi B', 'Nicki Minaj', 'Post Malone', 'Juice WRLD', '21 Savage', 
            'Lil Uzi Vert', 'XXXTentacion', 'J. Cole', 'Meek Mill', 'Tyga', 'Rick Ross', 'Gucci Mane', 'A$AP Rocky', 'A$AP Ferg', 'Playboi Carti', 
            'Trippie Redd', 'Lil Pump', 'Lil Yachty', 'Young Thug', 'Gunna', 'DaBaby', 'Roddy Ricch', 'Pop Smoke', 'NLE Choppa', 'Lil Tjay', 
            'Polo G', 'Blueface', 'Lil Skies', 'BlocBoy JB', 'Juicy J', 'Three 6 Mafia', 'T.I.', 'Ludacris', 'Wiz Khalifa', 'Mac Miller', 'Machine Gun Kelly'
        ],
        'funk': [
            'funk', 'brazilian funk', 'funk carioca', 'favela funk', 'MC Kevinho', 'Anitta', 'MC Livinho', 'MC Kevin O Chris', 'MC Kekel', 'Ludmilla', 
            'MC Guimê', 'MC Bin Laden', 'MC João', 'MC Loma e As Gêmeas Lacração', 'MC Fioti', 'Nego do Borel', 'MC Carol', 'Valesca Popozuda', 
            'MC G15', 'MC Lan', 'MC Mirella', 'MC Pikachu', 'MC Pedrinho', 'MC Davi', 'MC Don Juan', 'MC Brinquedo', 'MC Hariel', 'MC WM', 
            'MC Jottapê', 'MC Zaac', 'MC Marks', 'MC Cabelinho', 'MC Cacau', 'Tati Quebra Barraco', 'Mr. Catra', 'DJ Marlboro', 'DJ Rennan da Penha', 
            'DJ Polyvox', 'Bonde do Tigrão', 'Cidinho & Doca', 'MC Sapão', 'MC Marcinho', 'MC Koringa', 'MC Leozinho', 'MC Créu', 'MC Diguinho'
        ],
        'eletronica': [
            'eletrônica', 'edm', 'techno', 'house', 'trance', 'dubstep', 'David Guetta', 'Calvin Harris', 'Avicii', 'Tiesto', 'Skrillex', 'Martin Garrix', 
            'Deadmau5', 'Armin van Buuren', 'Swedish House Mafia', 'Steve Aoki', 'Dillon Francis', 'Diplo', 'Kygo', 'Zedd', 'Alan Walker', 
            'Hardwell', 'Afrojack', 'Nicky Romero', 'Marshmello', 'Oliver Heldens', 'Don Diablo', 'Above & Beyond', 'Paul van Dyk', 'Dash Berlin', 
            'Alesso', 'Axwell', 'Sebastian Ingrosso', 'Knife Party', 'Madeon', 'Porter Robinson', 'Krewella', 'Benny Benassi', 'Borgore', 
            'Flume', 'Illenium', 'RL Grime', 'Dada Life', 'Duke Dumont', 'Fedde Le Grand', 'Gareth Emery', 'Galantis', 'Lost Frequencies', 
            'Robin Schulz', 'Sam Feldt', 'Thomas Gold', 'Yellow Claw', 'W&W', 'Tritonal', 'Sander van Doorn', 'Kaskade', 'Laidback Luke'
        ],
        'sertanejo': [
            'sertanejo', 'sertanejo universitario', 'sertanejo pop', 'modao', 'Jorge & Mateus', 'Henrique & Juliano', 'Gusttavo Lima', 'Marília Mendonça', 
            'Maiara & Maraisa', 'Zé Neto & Cristiano', 'Wesley Safadão', 'Gustavo Mioto', 'Luan Santana', 'Michel Teló', 'César Menotti & Fabiano', 
            'Simone & Simaria', 'Fernando & Sorocaba', 'Chrystian & Ralf', 'Leandro & Leonardo', 'Chitãozinho & Xororó', 'Zezé Di Camargo & Luciano', 
            'João Paulo & Daniel', 'Bruno & Marrone', 'Victor & Leo', 'Matheus & Kauan', 'Munhoz & Mariano', 'João Bosco & Vinícius', 'Jads & Jadson', 
            'Hugo & Tiago', 'Humberto & Ronaldo', 'Edson & Hudson', 'Rick & Renner', 'Teodoro & Sampaio', 'Milionário & José Rico', 'Tonico & Tinoco', 
            'Pena Branca & Xavantinho', 'Inezita Barroso', 'Almir Sater', 'Sérgio Reis', 'Renato Teixeira', 'Roberta Miranda', 'Léo Canhoto & Robertinho', 
            'Dino Franco & Mouraí', 'Zilo & Zalo', 'Cascatinha & Inhana', 'Lourenço & Lourival', 'Pedro Bento & Zé da Estrada', 'Duduca & Dalvan', 
            'João Mineiro & Marciano', 'As Galvão', 'Irineu & Irineia', 'Tião Carreiro & Pardinho'
        ],
        'latina': [
            'latina', 'reggaeton', 'salsa', 'bachata', 'merengue', 'cumbia', 'Shakira', 'Daddy Yankee', 'Marc Anthony', 'Romeo Santos', 'Juanes', 
            'Enrique Iglesias', 'Maluma', 'J Balvin', 'Don Omar', 'Wisin & Yandel', 'Ricky Martin', 'Luis Fonsi', 'Ozuna', 'Bad Bunny', 'Karol G', 
            'Nicky Jam', 'Prince Royce', 'Celia Cruz', 'Héctor Lavoe', 'Rubén Blades', 'Tito Puente', 'Carlos Vives', 'Gloria Estefan', 'Jennifer Lopez', 
            'Pitbull', 'Anuel AA', 'Camila Cabello', 'Marcela Morelo', 'Pablo Alborán', 'David Bisbal', 'Fonseca', 'Jesse & Joy', 'Mana', 'Reik', 
            'CNCO', 'Gente de Zona', 'Nacho', 'Elvis Crespo', 'La India', 'Gilberto Santa Rosa', 'Victor Manuelle', 'Grupo Niche', 'Orquesta Guayacán', 
            'Joe Arroyo', 'Fruko y sus Tesos', 'La Sonora Ponceña', 'La Fania All-Stars', 'Aventura', 'Andy Montañez', 'Eddy Herrera', 'Johnny Ventura'
        ],
        'classica': [
            'clássica', 'classical', 'orchestra', 'symphony', 'piano', 'violin', 'Ludwig van Beethoven', 'Wolfgang Amadeus Mozart', 'Johann Sebastian Bach', 
            'Frederic Chopin', 'Antonio Vivaldi', 'Franz Schubert', 'Pyotr Ilyich Tchaikovsky', 'Igor Stravinsky', 'Gustav Mahler', 'Johannes Brahms', 
            'Richard Wagner', 'Franz Liszt', 'Joseph Haydn', 'Georg Friedrich Händel', 'Dmitri Shostakovich', 'Sergei Rachmaninoff', 'Sergei Prokofiev', 
            'Maurice Ravel', 'Claude Debussy', 'Felix Mendelssohn', 'Hector Berlioz', 'Edvard Grieg', 'Jean Sibelius', 'Antonín Dvořák', 'Ralph Vaughan Williams', 
            'Aaron Copland', 'Charles Ives', 'Samuel Barber', 'John Cage', 'Philip Glass', 'Steve Reich', 'Arvo Pärt', 'Krzysztof Penderecki', 'Leonard Bernstein', 
            'Giacomo Puccini', 'Gioachino Rossini', 'Gaetano Donizetti', 'Vincenzo Bellini', 'Jules Massenet', 'Camille Saint-Saëns', 'César Franck', 
            'Paul Dukas', 'Gabriel Fauré', 'Nikolai Rimsky-Korsakov', 'Mily Balakirev', 'Modest Mussorgsky', 'Alexander Borodin', 'Isaac Albéniz', 
            'Manuel de Falla', 'Joaquín Rodrigo', 'Erik Satie', 'Ottorino Respighi', 'Luciano Berio', 'Luigi Nono', 'Darius Milhaud', 'Francis Poulenc', 
            'Olivier Messiaen', 'György Ligeti', 'Béla Bartók', 'Zoltán Kodály'
        ],
        'pagode': [
            'pagode', 'samba de raiz', 'pagode romântico', 'partido alto', 'pagodinho', 'Zeca Pagodinho', 'Grupo Revelação', 'Fundo de Quintal', 'Thiaguinho', 
            'Sorriso Maroto', 'Exaltasamba', 'Péricles', 'Samba Pra Gente', 'Arlindo Cruz', 'Raça Negra', 'Só Pra Contrariar', 'Belo', 'Turma do Pagode', 
            'Pixote', 'Katinguelê', 'Negritude Junior', 'Molejo', 'Jorge Aragão', 'Beth Carvalho', 'Dudu Nobre', 'Alcione', 'Martinho da Vila', 
            'Dudu Nobre', 'Grupo Raça', 'Pique Novo', 'Grupo Bom Gosto', 'Reinaldo', 'Grupo Sensação', 'Katinguelê', 'Os Travessos', 'Netinho de Paula', 
            'Salgadinho', 'Sensação', 'Art Popular', 'Kiloucura', 'Almir Guineto', 'Adryana Ribeiro', 'Luiz Carlos', 'Xande de Pilares', 'Ferrugem', 
            'Marquinhos Sensação', 'Renatinho da Bahia', 'Grupo Nosso Sentimento', 'Grupo Tá na Mente', 'Grupo Clareou', 'Grupo Balacobaco', 
            'Grupo Disfarce', 'Grupo Kiloucura', 'Reinaldo', 'Grupo Nuwance', 'Grupo Pirraça', 'Grupo Vou Pro Sereno', 'Grupo Bom Gosto', 'Grupo Bokaloka'
        ]
    }


    # Converte o título para minúsculas para uma comparação case-insensitive
    titulo_lower = titulo.lower()

    # Verifica se algum padrão está presente no título
    for genero, palavras_chave in generos.items():
        for palavra_chave in palavras_chave:
            if re.search(r'\b' + remover_caracteres_especiais(palavra_chave) + r'\b', remover_caracteres_especiais(titulo_lower)):
                return genero

    return 'desconhecido'  # Caso não encontre correspondência

 

def obter_detalhes(song):
    song_query = song.get("webpage_url", "")
    duration_in_minutes = song.get('duration', 0) // 60
    canal = song.get('uploader', '')

    if duration_in_minutes <= 10 and 'thumbnail' in song and song_query and duration_in_minutes >= 2:
        genero = identificar_genero(remover_caracteres_especiais(song.get('title', '')))
        titulo = remover_caracteres_especiais(song.get('title', ''), 1)
        letra = 'Letra desconhecida'

        song_detail = {
            'id': song.get('id', ''),
            'nome': titulo,
            'url': song_query,
            'imagem': song.get('thumbnail', ''),
            'tempo': song.get('duration', 0),
            'views': song.get('view_count', 0),
            'like': song.get('like_count', 0),
            'genero': genero,
            'letra': letra
        }

        return song_detail
    else:
        return None




@search_bp.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data['query']

        # Verificar se os dados de entrada são válidos
        if data is None or 'query' not in data or not isinstance(data['query'], str) or not data['query'].strip():
            return jsonify({}), 400

        with ThreadPoolExecutor() as executor:
            future = executor.submit(buscar_musicas, query)
            song_details = future.result()

        return jsonify(song_details)

    except Exception as e:
        app.logger.error(f'Error processing search: {str(e)}')
        return jsonify({}), 500
