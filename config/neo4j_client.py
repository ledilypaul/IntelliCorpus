import os
from functools import lru_cache

from neo4j import Driver, GraphDatabase


@lru_cache(maxsize=1)
def get_neo4j_driver() -> Driver:
    """Crée et retourne un driver Neo4j singleton chargé depuis les variables d'environnement.

    Le lru_cache garantit que le driver n'est instancié qu'une seule fois,
    même si la fonction est appelée depuis plusieurs modules.

    Returns:
        Driver: driver Neo4j connecté via le protocole Bolt.

    Raises:
        KeyError: si NEO4J_URI, NEO4J_USER ou NEO4J_PASSWORD ne sont pas définis.
    """
    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))
