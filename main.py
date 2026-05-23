# main.py
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from schemas import ProdiCreate, ProdiUpdate, FakultasCreate, FakultasUpdate, UserAuth # Tambahkan UserAuth
from database import SessionLocal, engine

# Import Tambahan untuk Autentikasi & Env
import os
from dotenv import load_dotenv
import jwt
import datetime
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

# Memuat variabel dari file .env
load_dotenv()

# Inisialisasi aplikasi FastAPI
app = FastAPI(title="Praktikum Web API", version="1.0.0")

# Membuat semua tabel di database secara otomatis
models.Base.metadata.create_all(bind=engine)

# ==========================================
# KONFIGURASI KEAMANAN & JWT
# ==========================================
# Ambil SECRET_KEY dari .env
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_rahasia_default")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "rahasia_refresh")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Umur Token
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Inisialisasi library untuk hashing password
pwd_context = PasswordHash([BcryptHasher()])

# Dependency untuk mendapatkan koneksi database per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# DEPENDENCY PROTEKSI (Mengecek Token di Cookie)
def verify_token(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=403, detail="Akses ditolak. Access Token tidak ditemukan.")
    
    try:
        decoded_data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_data
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access Token kedaluwarsa. Silakan gunakan endpoint /refresh.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Access Token tidak valid.")


# ==========================================
# ENDPOINT AUTENTIKASI (AUTH)
# ==========================================

@app.post("/register", status_code=201, tags=["Auth"])
def register_user(user_data: UserAuth, db: Session = Depends(get_db)):
    try:
        # Cek apakah username sudah dipakai
        query_cek = text("SELECT id FROM users WHERE username = :u")
        cek_user = db.execute(query_cek, {"u": user_data.username}).fetchone()
        if cek_user:
            raise HTTPException(status_code=400, detail="Username sudah terdaftar")
            
        # Hash password
        hashed_pw = pwd_context.hash(user_data.password)
        
        # Simpan ke database MySQL menggunakan Raw Query
        query_insert = text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)")
        db.execute(query_insert, {"u": user_data.username, "p": hashed_pw, "r": "admin"})
        db.commit()
        return {"message": "Registrasi berhasil, silakan login"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login", tags=["Auth"])
def login_user(user_data: UserAuth, response: Response, db: Session = Depends(get_db)):
    query_user = text("SELECT * FROM users WHERE username = :u")
    user = db.execute(query_user, {"u": user_data.username}).mappings().fetchone()
    
    if not user or not pwd_context.verify(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Username atau password salah")
        
    # 1. Buat Access Token (Umur Pendek)
    access_payload = {
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # 2. Buat Refresh Token (Umur Panjang)
    refresh_payload = {
        "username": user["username"],
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    
    # 3. Set Keduanya di HttpOnly Cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
    
    return {"message": "Login berhasil, token telah diset."}

@app.post("/refresh", tags=["Auth"])
def refresh_access_token(request: Request, response: Response, db: Session = Depends(get_db)):
    # Ambil refresh token dari cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token tidak ditemukan. Silakan login kembali.")
        
    try:
        # Verifikasi Refresh Token menggunakan REFRESH_SECRET_KEY
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        
        # Ambil data user dari database (untuk memastikan user masih aktif/role terbaru)
        query_user = text("SELECT * FROM users WHERE username = :u")
        user = db.execute(query_user, {"u": username}).mappings().fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User tidak ditemukan.")
            
        # Buat Access Token BARU
        new_access_payload = {
            "username": user["username"],
            "role": user["role"],
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        new_access_token = jwt.encode(new_access_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        # Timpa access_token lama di cookie dengan yang baru
        response.set_cookie(key="access_token", value=new_access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        return {"message": "Access token berhasil diperbarui."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token kedaluwarsa. Silakan login kembali.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid.")

@app.post("/logout", tags=["Auth"])
def logout_user(response: Response):
    # Menghapus cookie access_token dan refresh_token dari browser
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logout berhasil, cookie telah dihapus."}


# ==========================================
# ENDPOINT YANG DILINDUNGI (PROTECTED)
# ==========================================

@app.get("/profil", tags=["Protected"])
def profil_user(user_info: dict = Depends(verify_token)):
    # user_info secara otomatis berisi data dari return fungsi verify_token
    return {
        "message": "Selamat datang di area rahasia",
        "data_login": user_info
    }


# ==========================================
# ENDPOINT UNTUK PRODI (SUDAH DIPROTEKSI)
# ==========================================

@app.get("/prodi/", status_code=200, tags=["Prodi"], description="Menampilkan data prodi")
def list_prodi(db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    query = text("SELECT * FROM prodi")
    data_prodi = db.execute(query).mappings().fetchall()
    return {"total": len(data_prodi), "data": data_prodi}

@app.post("/prodi/", status_code=201, tags=["Prodi"], description="Menambahkan data prodi baru")
def create_prodi(pro: ProdiCreate, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    try:
        query = text("INSERT INTO prodi VALUES (:pid, :pnama, :pfakultas)")
        db.execute(query, {"pid": pro.id, "pnama": pro.nama, "pfakultas": pro.fakultas})
        db.commit()
        return {"message": "Data berhasil disimpan", "data": pro}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/prodi/{prodi_id}", status_code=200, tags=["Prodi"], description="Memperbarui data prodi")
def update_prodi(prodi_id: str, pro: ProdiUpdate, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    try:
        query = text("UPDATE prodi SET nama=:pnama, fakultas=:pfakultas WHERE id=:pid")
        result = db.execute(query, {"pid": prodi_id, "pnama": pro.nama, "pfakultas": pro.fakultas})
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Prodi tidak ditemukan")
        return {"message": "Data berhasil diperbarui", "data": {"id": prodi_id, "nama": pro.nama, "fakultas": pro.fakultas}}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/prodi/{prodi_id}", status_code=200, tags=["Prodi"], description="Menghapus data prodi")
def delete_prodi(prodi_id: str, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    try:
        query = text("DELETE FROM prodi WHERE id=:pid")
        result = db.execute(query, {"pid": prodi_id})
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Prodi tidak ditemukan")
        return {"message": f"Data dengan ID {prodi_id} berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# ENDPOINT UNTUK FAKULTAS (SUDAH DIPROTEKSI)
# ==========================================

@app.get("/fakultas/", status_code=200, tags=["Fakultas"])
def list_fakultas(db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    query = text("SELECT * FROM fakultas")
    data = db.execute(query).mappings().fetchall()
    return {"total": len(data), "data": data}

@app.get("/fakultas/{id}", status_code=200, tags=["Fakultas"])
def get_fakultas(id: int, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    query = text("SELECT * FROM fakultas WHERE id = :id")
    data = db.execute(query, {"id": id}).mappings().fetchone()
    if not data:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan")
    return data

@app.post("/fakultas/", status_code=201, tags=["Fakultas"])
def create_fakultas(fkl: FakultasCreate, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    try:
        query = text("INSERT INTO fakultas (nama, keterangan) VALUES (:nama, :ket)")
        db.execute(query, {"nama": fkl.nama, "ket": fkl.keterangan})
        db.commit()
        return {"message": "Data fakultas berhasil disimpan"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/fakultas/{id}", status_code=200, tags=["Fakultas"])
def update_fakultas(id: int, fkl: FakultasUpdate, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    try:
        query = text("UPDATE fakultas SET nama=:nama, keterangan=:ket WHERE id=:id")
        result = db.execute(query, {"id": id, "nama": fkl.nama, "ket": fkl.keterangan})
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan")
        return {"message": "Data fakultas berhasil diperbarui"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/fakultas/{id}", status_code=200, tags=["Fakultas"])
def delete_fakultas(id: int, db: Session = Depends(get_db), user_info: dict = Depends(verify_token)): # Proteksi ditambahkan
    try:
        query = text("DELETE FROM fakultas WHERE id = :id")
        result = db.execute(query, {"id": id})
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan")
        return {"message": f"Fakultas dengan ID {id} berhasil dihapus"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))