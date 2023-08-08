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
    if client_type is None:
        client_type = CLIENT_TYPE

    if client_type == "POSTGRES":
        if POSTGRES_CONNECTION_STRING is None:
            raise EnvironmentError(
                "Postgres connection string not set in environment variables!"
            )
        if client is None:
            client = PostgresClient(POSTGRES_CONNECTION_STRING)
        return client
    else:
        if client is None:
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
        query = f"SELECT * FROM memories WHERE category=%s LIMIT %s OFFSET %s"
        self.client.cur.execute(query, (self.category, limit, offset))
        rows = self.client.cur.fetchall()
        
        # Convert rows to list of dictionaries
        columns = [desc[0] for desc in self.client.cur.description]
        return [dict(zip(columns, row)) for row in rows]


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

    def update(self, ids, embeddings=None, metadatas=None, documents=None):
        for id_, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
            self.client.update(self.category, id_, doc, meta)

    def upsert(self, ids, embeddings=None, metadatas=None, documents=None):
        self.add(ids, embeddings, metadatas, documents)

    def delete(self, ids=None, where=None, where_document=None):
        query = "DELETE FROM memories WHERE category=%s AND id=ANY(%s)"
        self.client.cur.execute(query, (self.category, ids))
        self.client.conn.commit()

class PostgresCategory:
    def __init__(self, name):
        self.name = name

class PostgresClient:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
        self.cur = self.conn.cursor()
        from pgvector.psycopg2 import register_vector

        register_vector(self.cur)  # Register PGVector functions
        self.model = SentenceTransformer("BAAI/bge-large-en")
        self._create_memories_table()

    def list_collections(self):
        self.cur.execute("SELECT DISTINCT category FROM memories")
        # return a collection object with the key 'name' with the value category for each row (collection.name)
        return [PostgresCategory(row) for row in self.cur.fetchall()]
    
    def delete_collection(self, category):
        self.cur.execute("DELETE FROM memories WHERE category=%s", (category,))
        self.conn.commit()
        
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
        self.conn.commit()

    def get_or_create_collection(self, category):
        return PostgresCollection(category, self)

    def insert_memory(self, category, document, metadata={}, embedding=None):
        metadata_string = json.dumps(metadata)  # Convert the dict to a JSON string
        query = """
        INSERT INTO memories (category, document, metadata, embedding) VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        self.cur.execute(query, (category, document, metadata_string, embedding))
        self.conn.commit()
        return self.cur.fetchone()[0]

    def create_embedding(self, document):
        return self.model.encode(document)

    def add(self, category, documents, metadatas, ids):
        with self.connection.cursor() as cur:
            for doc, meta, id_ in zip(documents, metadatas, ids):
                embedding = self.create_embedding(doc)
                cur.execute(
                    f"""
                    INSERT INTO {category} (id, document, metadata, embedding)
                    VALUES (%s, %s, %s, %s)
                """,
                    (id_, doc, meta, embedding),
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
                    FROM {category}
                    WHERE embedding <@- %s
                    ORDER BY embedding <-> %s
                    LIMIT %s
                """,
                    (emb, emb, emb, n_results),
                )
                results.extend(cur.fetchall())
        return results

    def update(self, category, id_, document=None, metadata=None):
        with self.connection.cursor() as cur:
            if document:
                embedding = self.create_embedding(document)
                cur.execute(
                    f"""
                    UPDATE {category}
                    SET document=%s, embedding=%s, metadata=%s
                    WHERE id=%s
                """,
                    (document, embedding, metadata, id_),
                )
            else:
                cur.execute(
                    f"""
                    UPDATE {category}
                    SET metadata=%s
                    WHERE id=%s
                """,
                    (metadata, id_),
                )
            self.connection.commit()

    def close(self):
        self.cur.close()
        self.conn.close()
