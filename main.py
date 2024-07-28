from flask import Flask, request, jsonify
import yt_dlp
from difflib import SequenceMatcher
from pytube import YouTube
from moviepy.editor import *

from flask import request, jsonify
from datetime import datetime, timedelta
from unidecode import unidecode
import sqlite3
from youtube_dl import YoutubeDL
import json
import re
import speech_recognition as sr

from cryptography.fernet import Fernet
import os
import unicodedata
from flask_cors import CORS
import emoji

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment


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
                like INTEGER DEFAULT 0,
                genero TEXT,
                letra TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print("Erro ao inicializar o banco de dados:", e)   


@app.route('/')
def home():
    return "Server está Online: OneSong Server!"



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)