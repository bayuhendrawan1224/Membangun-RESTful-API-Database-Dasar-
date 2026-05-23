# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv

load_dotenv()  # Memuat variabel lingkungan dari file .env
# Format URL: mysql+pymysql://username:password@host:port/nama_database
# Sesuaikan password jika root Anda memiliki password (contoh: root:@)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL",
"mysql+pymysql://root:@localhost:3306/siakad")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()