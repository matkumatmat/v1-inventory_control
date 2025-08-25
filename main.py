import tracemalloc
tracemalloc.start()

# backends/main.py

# --- FIX: Tambahkan dua baris ini di paling atas ---
from dotenv import load_dotenv
load_dotenv(override=True)
# ----------------------------------------------------

from app import create_app

# Fungsi ini yang akan dipanggil oleh Uvicorn
# Uvicorn akan mencari variabel 'app' secara default jika 'factory=True' digunakan
app = create_app
