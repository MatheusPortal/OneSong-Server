"One-API Music V1 - Documentação

One-API Music V1
Uma API que permite a busca, extração e exibição de músicas, letras e áudios. A API centraliza a busca por músicas em diversas fontes, retornando letras e arquivos de áudio para uma experiência integrada. O objetivo é oferecer uma solução única para quem deseja encontrar músicas, sincronizar letras e baixar faixas diretamente de plataformas como o YouTube.

Instalação
Requisitos:

Python 3.10+
SQLite
Flask 2.3.2+
Flask-Cors 4.0.1+
ffmpeg

Funcionalidades
Busca de Músicas: Pesquisa no banco de dados local e no YouTube.
Extração de Letras: Retorna letras de músicas sincronizadas.
Download de Áudios: Faz o download de faixas diretamente do YouTube.
Integração com API: Busca integrada em diversas plataformas para fornecer detalhes completos sobre músicas.


Uso
Após iniciar a aplicação, você pode realizar buscas utilizando a rota /search fornecendo o nome da música ou artista. A API retornará um JSON com informações sobre a música, letra e um link para o download do áudio.
" 
