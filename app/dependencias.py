# Importações padrão
import os
import json
import re
import unicodedata
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# Importações de bibliotecas de terceiros
from flask import request, jsonify, Blueprint, current_app as app
from flask_cors import CORS
from pydub import AudioSegment
from cryptography.fernet import Fernet
import requests
from bs4 import BeautifulSoup
import yt_dlp
from pytube import YouTube
from moviepy.editor import *
import sqlite3
import speech_recognition as sr
import unidecode
import emoji
from flask import Flask

