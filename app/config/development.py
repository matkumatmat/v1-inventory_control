# app/config/development.py

import os
from dotenv import load_dotenv

# Muat variabel dari .env
load_dotenv()

class DevelopmentConfig:
    """
    Development configuration
    """
    # Sekarang os.getenv akan berhasil mendapatkan nilainya
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")