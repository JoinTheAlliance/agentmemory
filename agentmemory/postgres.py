import json
import psycopg2


class PostgresCollection:
    def __init__(self, category, client):
        self.category = category
        self.client = client

    def count(self):
        self.client.ensure_table_exists(self.category)
        table_name = self.client._table_name(self.category)

        query = f"SELECT COUNT(*) FROM {table_name}"
        self.client.cur.execute(query)

        return self.client.cur.fetchone()[0]

    def add(self, ids, documents=None, metadatas=None, embeddings=None):
        if embeddings is None:
            for id_, document, metadata in zip(ids, documents, metadatas):
                self.client.insert_memory(self.category, document, metadata)
        else:
            for id_, document, metadata, emb in zip(
                ids, documents, metadatas, embeddings
            ):
                self.client.insert_memory(self.category, document, metadata, emb)

    def get(
        self,
        ids=None,
        where=None,
        limit=None,
        offset=None,
        where_document=None,
        include=["metadatas", "documents"],
    ):
        category = self.category
        table_name = self.client._table_name(category)
        if not ids:
            if limit is None:
                limit = 100  # or another default value
            if offset is None:
                offset = 0

            query = f"SELECT * FROM {table_name} LIMIT %s OFFSET %s"
            params = (limit, offset)

        else:
            if not all(isinstance(i, str) or isinstance(i, int) for i in ids):
                raise Exception(
                    "ids must be a list of integers or strings representing integers"
                )

            if limit is None:
                limit = len(ids)
            if offset is None:
                offset = 0

            table_name = self.client._table_name(category)
            ids = [int(i) for i in ids]

            query = f"SELECT * FROM {table_name} WHERE id=ANY(%s) LIMIT %s OFFSET %s"
            params = (ids, limit, offset)

        self.client.cur.execute(query, params)
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
            for id_, document, metadata in zip(ids, documents, metadatas):
                self.client.update(self.category, id_, document, metadata)
        else:
            for id_, document, metadata, emb in zip(
                ids, documents, metadatas, embeddings
            ):
                self.client.update(self.category, id_, document, metadata, emb)

    def upsert(self, ids, documents=None, metadatas=None, embeddings=None):
        self.add(ids, documents, metadatas, embeddings)

    def delete(self, ids=None, where=None, where_document=None):
        table_name = self.client._table_name(self.category)
        # check if table exists
        self.client.ensure_table_exists(self.category)

        # Base of the query
        query = f"DELETE FROM {table_name}"
        params = []

        conditions = []

        if ids is not None:
            if not all(isinstance(i, (int, str)) and str(i).isdigit() for i in ids):
                raise Exception(
                    "ids must be a list of integers or strings representing integers"
                )
            ids = [int(i) for i in ids]
            conditions.append("id=ANY(%s::int[])")
            params.append(ids)

        if where_document is not None:
            if "$contains" in where_document:
                conditions.append("document LIKE %s")
                params.append(f"%{where_document['$contains']}%")
            # You can add more operators for 'where_document' here if needed

        if where is not None:
            for key, value in where.items():
                conditions.append(f"{key}=%s")
                params.append(value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        else:
            raise Exception("No valid conditions provided for deletion.")

        self.client.cur.execute(query, tuple(params))
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

        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _table_name(self, category):
        return f"memory_{category}"

    def ensure_table_exists(self, category):
        table_name = self._table_name(category)
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                document TEXT NOT NULL,
                metadata JSONB,
                embedding VECTOR(1024)
            )
        """
        )
        self.connection.commit()

    def _ensure_metadata_columns_exist(self, category, metadata):
        table_name = self._table_name(category)
        for key in metadata.keys():
            self.cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_catalog.pg_attribute 
                    WHERE attrelid = %s::regclass 
                    AND attname = %s 
                    AND NOT attisdropped
                )
            """,
                (table_name, key),
            )
            exists = self.cur.fetchone()[0]
            if not exists:
                self.cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {key} TEXT")
                self.connection.commit()

    def list_collections(self):
        self.cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )
        return [
            PostgresCategory(row[0].split("_")[1])
            for row in self.cur.fetchall()
            if row[0].startswith("memory_")
        ]

    def get_collection(self, category):
        return PostgresCollection(category, self)

    def delete_collection(self, category):
        table_name = self._table_name(category)
        self.cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.connection.commit()

    def get_or_create_collection(self, category):
        return PostgresCollection(category, self)

    def insert_memory(self, category, document, metadata={}, embedding=None, id=None):
        self.ensure_table_exists(category)
        self._ensure_metadata_columns_exist(category, metadata)
        table_name = self._table_name(category)

        metadata_string = json.dumps(metadata)  # Convert the dict to a JSON string
        if embedding is None:
            embedding = self.create_embedding(document)

        # if the id is None, get the length of the table by counting the number of rows in the category
        if id is None:
            id = self.get_or_create_collection(category).count()

        query = f"""
        INSERT INTO {table_name} (id, document, metadata, embedding) VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        self.cur.execute(query, (id, document, metadata_string, embedding))
        self.connection.commit()
        return self.cur.fetchone()[0]

    def create_embedding(self, document):
        return self.model.encode(document, normalize_embeddings=True)

    def add(self, category, documents, metadatas, ids):
        self.ensure_table_exists(category)
        table_name = self._table_name(category)
        with self.connection.cursor() as cur:
            for document, metadata, id_ in zip(documents, metadatas, ids):
                self._ensure_metadata_columns_exist(category, metadata)
                embedding = self.create_embedding(document)
                cur.execute(
                    f"""
                    INSERT INTO {table_name} (id, document, metadata, embedding)
                    VALUES (%s, %s %s, %s)
                """,
                    (id_, document, metadata, embedding),
                )
            self.connection.commit()

    def query(self, category, query_texts, n_results=5):
        embeddings = [self.create_embedding(q) for q in query_texts]
        results = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "embeddings": [],
            "distances": [],
        }
        self.ensure_table_exists(category)
        table_name = self._table_name(category)
        with self.connection.cursor() as cur:
            for emb in embeddings:
                cur.execute(
                    f"""
                    SELECT id, document, metadata, embedding, embedding <-> %s AS distance
                    FROM {table_name}
                    ORDER BY embedding <-> %s
                    LIMIT %s
                """,
                    (emb, emb, n_results),
                )
                rows = cur.fetchall()
                for row in rows:
                    results["ids"].append(row[0])
                    results["documents"].append(row[1])
                    results["metadatas"].append(row[2])
                    results["embeddings"].append(row[3])
                    results["distances"].append(row[4])
        return results

    def update(self, category, id_, document=None, metadata=None, embedding=None):
        self.ensure_table_exists(category)
        table_name = self._table_name(category)
        with self.connection.cursor() as cur:
            if document:
                # if metadata is a dict, convert it to a JSON string
                if isinstance(metadata, dict):
                    metadata = json.dumps(metadata)
                if embedding is None:
                    embedding = self.create_embedding(document)
                cur.execute(
                    f"""
                    UPDATE {table_name}
                    SET document=%s, embedding=%s, metadata=%s
                    WHERE id=%s
                """,
                    (document, embedding, metadata, id_),
                )
            else:
                cur.execute(
                    f"""
                    UPDATE {table_name}
                    SET metadata=%s
                    WHERE id=%s
                """,
                    (metadata, id_),
                )
            self.connection.commit()

    def close(self):
        self.cur.close()
        self.connection.close()
