# models.py
# Pastikan Integer sudah di-import di baris bawah ini
from sqlalchemy import Column, String, Integer
from database import Base

class Prodi(Base):
    __tablename__ = "prodi"
    
    id = Column(String(10), primary_key=True, index=True) # Sesuaikan tipe jika sebelumnya String
    nama = Column(String(100))
    fakultas = Column(String(100))

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255)) 
    role = Column(String(20), default="user")


class Fakultas(Base):
    __tablename__ = "fakultas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nama = Column(String(100), nullable=False)
    keterangan = Column(String(255))