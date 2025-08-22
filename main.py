# backends/main.py
from app import create_app

# Fungsi ini yang akan dipanggil oleh Uvicorn
def get_app():
    return create_app()