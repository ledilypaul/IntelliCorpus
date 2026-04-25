import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from typing import Tuple, Dict

# Charger une seule fois au début du module
load_dotenv()

class DBConfig:
    """Centralise la configuration et la validation."""
    def __init__(self):
        self.user = os.getenv('POSTGRES_USER')
        self.password = os.getenv('POSTGRES_PASSWORD')
        self.host = os.getenv('POSTGRES_HOST')
        self.port = os.getenv('POSTGRES_PORT')
        self.name = os.getenv('POSTGRES_DB')
        self.validate()

    def validate(self):
        missing = [k for k, v in self.__dict__.items() if not v]
        if missing:
            raise ValueError(f"Variables d'environnement manquantes : {', '.join(missing)}")

# Instance unique pour éviter de re-valider partout
_config = DBConfig()

# On crée l'engine une seule fois (Singleton)
_engine = None

def get_db_engine() -> Engine:
    """Retourne l'engine SQLAlchemy (créé uniquement au premier appel)."""
    global _engine
    if _engine is None:
        url = f"postgresql+psycopg2://{_config.user}:{_config.password}@{_config.host}:{_config.port}/{_config.name}"
        _engine = create_engine(url, pool_pre_ping=True) # pool_pre_ping vérifie si la connexion est tjs vivante
    return _engine

def get_jdbc_props() -> Tuple[str, Dict[str, str]]:
    """Retourne l'URL JDBC et les propriétés pour Spark/Java."""
    jdbc_url = f"jdbc:postgresql://{_config.host}:{_config.port}/{_config.name}"
    connection_props = {
        "user": _config.user,
        "password": _config.password,
        "driver": "org.postgresql.Driver"
    }
    return jdbc_url, connection_props