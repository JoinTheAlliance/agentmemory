import os
import json

import chromadb
import psycopg2
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

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


class PostgresCollection:
    def __init__(self, category, client):
        self.category = category
        self.client = client

    def count(self):
        self.client.cur.execute(
            f"SELECT COUNT(*) FROM memories WHERE category=%s", (self.category,)
        )
        return self.client.cur.fetchone()[0]

    def add(self, ids, embeddings=None, metadatas=None, documents=None):
        if embeddings is None:
            for id_, doc, meta in zip(ids, documents, metadatas):
                self.client.insert_memory(self.category, doc, meta)
        else:
            for id_, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
                self.client.insert_memory(self.category, doc, meta, emb)

    def get(
        self,
        ids=None,
        where=None,
        limit=None,
        offset=None,
        where_document=None,
        include=["metadatas", "documents"],
    ):
        if ids:
            if not all(isinstance(i, str) or isinstance(i, int) for i in ids):
                raise Exception("ids must be a list of integers or strings representing integers")
        
            # Map ids to integers
            ids_array = ",".join(map(str, [int(i) for i in ids]))

            # Adjusting the query to cast the entire ARRAY after it's constructed
            query = f"SELECT * FROM memories WHERE category=%s AND id=ANY(ARRAY[{ids_array}]::integer[]) LIMIT %s OFFSET %s"
            self.client.cur.execute(query, (self.category, limit, offset))

        else:
            query = f"SELECT * FROM memories WHERE category=%s LIMIT %s OFFSET %s"
            self.client.cur.execute(query, (self.category, limit, offset))
        rows = self.client.cur.fetchall()
        
        # Convert rows to list of dictionaries
        columns = [desc[0] for desc in self.client.cur.description]
        result = [dict(zip(columns, row)) for row in rows]

        return {
            "ids": [row["id"] for row in result],
            "documents": [row["document"] for row in result],
            "metadatas": [row["metadata"] for row in result],
        }



    def peek(self, limit=10):
        return self.get(limit=limit)

    def query(
        self,
        query_embeddings=None,
        query_texts=None,
        n_results=10,
        where=None,
        where_document=None,
        include=["metadatas", "documents", "distances"],
    ):
        return self.client.query(self.category, query_texts, n_results)

    def update(self, ids, documents=None, metadatas=None, embeddings=None):
        # if embeddings is not None
        if embeddings is None:
            for id_, doc, meta in zip(ids, documents, metadatas):
                self.client.update(self.category, id_, doc, meta)
        else:
            for id_, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
                self.client.update(self.category, id_, doc, meta, emb)

    def upsert(self, ids, embeddings=None, metadatas=None, documents=None):
        self.add(ids, embeddings, metadatas, documents)

    def delete(self, ids=None, where=None, where_document=None):
        ids = [int(i) for i in ids]
        query = "DELETE FROM memories WHERE category=%s AND id=ANY(%s::int[])"
        self.client.cur.execute(query, (self.category, ids))
        self.client.connection.commit()


class PostgresCategory:
    def __init__(self, name):
        self.name = name


class PostgresClient:
    def __init__(self, connection_string):
        self.connection = psycopg2.connect(connection_string)
        self.cur = self.connection.cursor()
        from pgvector.psycopg2 import register_vector

        register_vector(self.cur)  # Register PGVector functions
        self.model = SentenceTransformer("BAAI/bge-large-en")
        self._create_memories_table()

    def list_collections(self):
        self.cur.execute("SELECT DISTINCT category FROM memories")
        return [PostgresCategory(row) for row in self.cur.fetchall()]

    def get_collection(self, category):
        return PostgresCollection(category, self)

    def delete_collection(self, category):
        print("deleting collection", category)
        self.cur.execute("DELETE FROM memories WHERE category=%s", (category,))
        self.connection.commit()

    def _create_memories_table(self):
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            category TEXT NOT NULL,
            document TEXT NOT NULL,
            metadata JSONB,
            embedding VECTOR(1024)
        )
        """
        )
        self.connection.commit()

    def get_or_create_collection(self, category):
        return PostgresCollection(category, self)

    def insert_memory(self, category, document, metadata={}, embedding=None):
        metadata_string = json.dumps(metadata)  # Convert the dict to a JSON string
        if embedding is None:
            embedding = self.create_embedding(document)

        query = """
        INSERT INTO memories (category, document, metadata, embedding) VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        self.cur.execute(query, (category, document, metadata_string, embedding))
        self.connection.commit()
        return self.cur.fetchone()[0]

    def create_embedding(self, document):
        return self.model.encode(document)

    def add(self, category, documents, metadatas, ids):
        with self.connection.cursor() as cur:
            for doc, meta, id_ in zip(documents, metadatas, ids):
                embedding = self.create_embedding(doc)
                cur.execute(
                    """
                    INSERT INTO memories (id, category, document, metadata, embedding)
                    VALUES (%s, %s %s, %s, %s)
                """,
                    (id_, category, doc, meta, embedding),
                )
            self.connection.commit()

    def query(self, category, query_texts, n_results=5):
        embeddings = [self.create_embedding(q) for q in query_texts]
        results = []
        with self.connection.cursor() as cur:
            for emb in embeddings:
                cur.execute(
                    f"""
                    SELECT id, document, metadata, embedding <-> %s AS distance
                    FROM memories
                    WHERE category = %s
                    ORDER BY embedding <-> %s
                    LIMIT %s
                """,
                    (emb, category, emb, n_results),
                )
                results.extend(cur.fetchall())
        return results

    def update(self, category, id_, document=None, metadata=None, embedding=None):
        with self.connection.cursor() as cur:
            if document:
                print("updating document")
                print(document)
                print(metadata)
                # if metadata is a dict, convert it to a JSON string
                if isinstance(metadata, dict):
                    metadata = json.dumps(metadata)
                print(id_)
                if embedding is None:
                    embedding = self.create_embedding(document)
                cur.execute(
                    f"""
                    UPDATE memories
                    SET document=%s, embedding=%s, metadata=%s
                    WHERE id=%s AND category='{category}'
                """,
                    (document, embedding, metadata, id_),
                )
            else:
                cur.execute(
                    f"""
                    UPDATE memories
                    SET metadata=%s
                    WHERE id=%s AND category='{category}'
                """,
                    (metadata, id_),
                )
            self.connection.commit()

    def close(self):
        self.cur.close()
        self.connection.close()
