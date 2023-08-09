import os
import json

import chromadb
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from agentmemory.postgres import PostgresClient

load_dotenv()


DEFAULT_CLIENT_TYPE = "CHROMA"
CLIENT_TYPE = os.environ.get("CLIENT_TYPE", DEFAULT_CLIENT_TYPE)
STORAGE_PATH = os.environ.get("STORAGE_PATH", "./memory")
POSTGRES_CONNECTION_STRING = os.environ.get("POSTGRES_CONNECTION_STRING")

client = None


def get_client(client_type=None, *args, **kwargs):
    global client
    if client is not None:
        return client

    if client_type is None:
        client_type = CLIENT_TYPE

    if client_type == "POSTGRES":
        if POSTGRES_CONNECTION_STRING is None:
            raise EnvironmentError(
                "Postgres connection string not set in environment variables!"
            )
        client = PostgresClient(POSTGRES_CONNECTION_STRING)
    else:
        client = chromadb.PersistentClient(path=STORAGE_PATH, *args, **kwargs)

    return client