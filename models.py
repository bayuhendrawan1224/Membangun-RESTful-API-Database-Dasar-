# models.py
# Pastikan Integer sudah di-import di baris bawah ini
from sqlalchemy import Column, String, Integer 
from database import Base

class Prodi(Base):
    __tablename__ = "prodi"
    
    id = Column(String(10), primary_key=True, index=True)
    nama = Column(String(100))
    fakultas = Column(String(100))

# Entitas Fakultas untuk Tugas Praktikum
class Fakultas(Base):
    __tablename__ = "fakultas"
    
    id = Column(Integer, primary_key=True, autoincrement=True) # Sekarang Integer sudah dikenali
    nama = Column(String(100), nullable=False)
    keterangan = Column(String(255))