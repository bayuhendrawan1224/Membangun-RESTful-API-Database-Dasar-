# schemas.py
from pydantic import BaseModel
from typing import Optional

class UserAuth(BaseModel):
    username: str
    password: str
    

# --- SCHEMA PRODI ---
class ProdiCreate(BaseModel):
    id: str
    nama: str
    fakultas: str

class ProdiUpdate(BaseModel):
    nama: str
    fakultas: str

# --- SCHEMA FAKULTAS ---
# Pastikan 'class' dimulai dari awal baris (tidak menjorok ke dalam)
class FakultasCreate(BaseModel):
    nama: str
    keterangan: Optional[str] = None

class FakultasUpdate(BaseModel):
    nama: str
    keterangan: Optional[str] = None