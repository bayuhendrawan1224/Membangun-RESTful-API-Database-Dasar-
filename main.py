# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import models
from schemas import ProdiCreate, ProdiUpdate, FakultasCreate, FakultasUpdate
from database import SessionLocal, engine

# Inisialisasi aplikasi FastAPI
app = FastAPI(title="Praktikum Web API", version="1.0.0")

# Membuat semua tabel di database secara otomatis
models.Base.metadata.create_all(bind=engine)

# Dependency untuk mendapatkan koneksi database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# ENDPOINT UNTUK PRODI
# ==========================================

@app.get("/prodi/", status_code=200, tags=["Prodi"], description="Menampilkan data prodi")
def list_prodi(db: Session = Depends(get_db)):
    query = text("SELECT * FROM prodi")
    data_prodi = db.execute(query).mappings().fetchall()
    return {"total": len(data_prodi), "data": data_prodi}

@app.post("/prodi/", status_code=201, tags=["Prodi"], description="Menambahkan data prodi baru")
def create_prodi(pro: ProdiCreate, db: Session = Depends(get_db)):
    try:
        query = text("INSERT INTO prodi VALUES (:pid, :pnama, :pfakultas)")
        db.execute(query, {"pid": pro.id, "pnama": pro.nama, "pfakultas": pro.fakultas})
        db.commit()
        return {"message": "Data berhasil disimpan", "data": pro}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/prodi/{prodi_id}", status_code=200, tags=["Prodi"], description="Memperbarui data prodi")
def update_prodi(prodi_id: str, pro: ProdiUpdate, db: Session = Depends(get_db)):
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
def delete_prodi(prodi_id: str, db: Session = Depends(get_db)):
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
# ENDPOINT UNTUK FAKULTAS (TUGAS PRAKTIKUM)
# ==========================================

@app.get("/fakultas/", status_code=200, tags=["Fakultas"])
def list_fakultas(db: Session = Depends(get_db)):
    query = text("SELECT * FROM fakultas")
    data = db.execute(query).mappings().fetchall()
    return {"total": len(data), "data": data}

@app.get("/fakultas/{id}", status_code=200, tags=["Fakultas"])
def get_fakultas(id: int, db: Session = Depends(get_db)):
    query = text("SELECT * FROM fakultas WHERE id = :id")
    data = db.execute(query, {"id": id}).mappings().fetchone()
    if not data:
        raise HTTPException(status_code=404, detail="Fakultas tidak ditemukan")
    return data

@app.post("/fakultas/", status_code=201, tags=["Fakultas"])
def create_fakultas(fkl: FakultasCreate, db: Session = Depends(get_db)):
    try:
        query = text("INSERT INTO fakultas (nama, keterangan) VALUES (:nama, :ket)")
        db.execute(query, {"nama": fkl.nama, "ket": fkl.keterangan})
        db.commit()
        return {"message": "Data fakultas berhasil disimpan"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/fakultas/{id}", status_code=200, tags=["Fakultas"])
def update_fakultas(id: int, fkl: FakultasUpdate, db: Session = Depends(get_db)):
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
def delete_fakultas(id: int, db: Session = Depends(get_db)):
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