# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Format URL: mysql+pymysql://username:password@host:port/nama_database
# Sesuaikan password jika root Anda memiliki password (contoh: root:1234567890)
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost:3306/siakad"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()