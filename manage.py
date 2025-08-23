# backends/manage.py

# --- FIX: Tambahkan dua baris ini di paling atas ---
from dotenv import load_dotenv
load_dotenv()
# ----------------------------------------------------

import asyncio
import typer
import uvicorn
from typing_extensions import Annotated

# NOTE: File ini berfungsi seperti manage.py di Flask, tapi untuk project FastAPI.
# Kita menggunakan Typer, library dari developer FastAPI, untuk membuat command CLI.

# Inisialisasi Typer, "penerjemah" command line kita
cli = typer.Typer(
    help="Manajemen CLI untuk aplikasi WMS FastAPI."
)

# --- Database Commands ---

@cli.command()
def init_db():
    """
    Inisialisasi database dan membuat semua tabel.
    Membaca metadata dari semua model yang diimpor.
    """
    # Import dependency di dalam fungsi agar tidak dieksekusi saat startup
    from app.database import Base, async_engine

    # Penting: Impor semua modul yang berisi model SQLAlchemy
    # agar Base.metadata bisa mendeteksi semua tabel.
    # Sesuaikan dengan nama file model yang kamu punya.
    from app.models import (
        user, warehouse, product, consignment, contract, 
        customer, shipment, salesorder, picking, packing_slip,
        helper # Tambahkan semua file modelmu di sini
    )

    async def create_tables():
        """Fungsi async untuk membuat tabel."""
        async with async_engine.begin() as conn:
            typer.echo("Membuat semua tabel sesuai models...")
            await conn.run_sync(Base.metadata.create_all)
        typer.secho("✅ Database berhasil diinisialisasi.", fg=typer.colors.GREEN)

    # Menjalankan fungsi async menggunakan asyncio.run()
    asyncio.run(create_tables())

# --- User Management Commands ---

@cli.command()
def create_admin(
    username: Annotated[str, typer.Argument(help="Username untuk admin baru.")],
    email: Annotated[str, typer.Argument(help="Email untuk admin baru (harus unik).")],
    password: Annotated[str, typer.Argument(help="Password untuk admin baru.")]
):
    """
    Membuat user baru dengan role 'admin'.
    """
    # Import dependency di dalam fungsi
    from app.database import get_db_session
    from app.services.auth.user_service import UserService
    from app.schemas.user import UserCreateSchema
    from app.services.exceptions import ValidationError

    async def add_admin_user():
        """Fungsi async untuk menambah admin."""
        typer.echo(f"Mencoba membuat admin '{username}'...")
        # Kita butuh session database untuk berinteraksi dengan DB
        async for session in get_db_session():
            try:
                user_service = UserService(session)
                user_schema = UserCreateSchema(
                    username=username,
                    email=email,
                    password=password,
                    role='admin', # Hardcode role sebagai admin
                    is_active=True,
                    full_name=username.capitalize() # Default full_name
                )
                new_user = await user_service.create_user(user_schema)
                typer.secho(f"✅ Admin '{new_user.username}' berhasil dibuat!", fg=typer.colors.GREEN)
            except ValidationError as e:
                typer.secho(f"🔥 Gagal: Validasi error - {e}", fg=typer.colors.RED)
            except Exception as e:
                typer.secho(f"🔥 Gagal membuat admin: {e}", fg=typer.colors.RED)
            finally:
                # Pastikan session selalu ditutup
                await session.close()
    
    # Menjalankan fungsi async
    asyncio.run(add_admin_user())


# --- Server Commands ---

@cli.command()
def run(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True
):
    """
    Menjalankan development server Uvicorn.
    Ini adalah pengganti 'flask run'.
    """
    typer.echo(f"🚀 Menjalankan server di http://{host}:{port}")
    # Kita menunjuk ke 'app' di dalam file 'main.py'
    # Pastikan kamu punya file main.py di root backends/
    uvicorn.run("main:app", host=host, port=port, reload=reload, factory=True)


if __name__ == "__main__":
    cli()
