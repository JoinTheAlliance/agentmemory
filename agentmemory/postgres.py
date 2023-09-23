from __future__ import annotations
from pathlib import Path
import os
from functools import reduce
from itertools import repeat

import psycopg2

from .client import AgentMemory, CollectionMemory, AgentCollection
from .check_model import check_model, infer_embeddings
import agentlogger

def parse_metadata(where):
    where = where or {}
    metadata = {}
    for key, value in where.items():
        if key[0] != "$":
            metadata[key] = value
        if isinstance(value, dict):
            metadata.update(parse_metadata(value))
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    metadata.update(parse_metadata(item))
    return metadata


def handle_and_condition(and_conditions):
    conditions = []
    params = []
    for condition in and_conditions:
        for key, value in condition.items():
            for operator, operand in value.items():
                sql_operator = get_sql_operator(operator)
                conditions.append(f"{key} {sql_operator} %s")
                params.append(operand)
    return conditions, params


def handle_or_condition(or_conditions):
    or_groups = []
    params = []
    for condition in or_conditions:
        conditions, new_params = handle_and_condition([condition])
        or_groups.append(" AND ".join(conditions))
        params.extend(new_params)
    return f"({') OR ('.join(or_groups)})", params


def get_sql_operator(operator):
    if operator == "$eq":
        return "="
    elif operator == "$ne":
        return "!="
    elif operator == "$gt":
        return ">"
    elif operator == "$lt":
        return "<"
    else:
        raise ValueError(f"Operator {operator} not supported")

def parse_conditions(where=None, where_document=None, ids=None):
    conditions = []
    params = []
    if where_document is not None:
        if where_document.get("$contains", None) is not None:
            where_document = where_document["$contains"]
        conditions.append("document LIKE %s")
        params.append(f"%{where_document}%")

    if where:
        for key, value in where.items():
            if key == "$and":
                new_conditions, new_params = handle_and_condition(value)
                conditions.extend(new_conditions)
                params.extend(new_params)
            elif key == "$or":
                or_condition, new_params = handle_or_condition(value)
                conditions.append(or_condition)
                params.extend(new_params)
            elif key == "$contains":
                conditions.append(f"document LIKE %s")
                params.append(f"%{value}%")
            else:
                conditions.append(f"{key}=%s")
                params.append(str(value))

    if ids:
        if not all(isinstance(i, str) or isinstance(i, int) for i in ids):
            raise Exception(
                "ids must be a list of integers or strings representing integers"
            )
        ids = [int(i) for i in ids]
        conditions.append("id=ANY(%s::int[])")  # Added explicit type casting
        params.append(ids)

    return conditions, params

class PostgresCollection(CollectionMemory):
    def __init__(self, category, client: PostgresClient, metadata=None):
        self.category = category
        self.client = client
        self.metadata = metadata or {}
        client.ensure_table_exists(category)
        if metadata:
            client._ensure_metadata_columns_exist(category, metadata)

    def _validate_metadata(self, metadata):
        if new_columns := set(metadata) - set(self.metadata):
            agentlogger.log(f"Undeclared metadata {', '.join(new_columns)} for collection {self.category}")
            self.client._ensure_metadata_columns_exist(self.category, metadata)
            self.metadata.update(metadata)

    def count(self):
        table_name = self.client._table_name(self.category)

        query = f"SELECT COUNT(*) FROM {table_name}"
        self.client.cur.execute(query)

        return self.client.cur.fetchone()[0]

    def add(self, ids=None, documents=None, metadatas=None, embeddings=None):
        # dropping ids, using database serial
        embeddings = embeddings or repeat(None)
        metadatas = metadatas or repeat({})
        for document, metadata, emb in zip(
            documents, metadatas, embeddings
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
        # TODO: Mirrors Chroma API, but could be optimized a lot
        category = self.category
        table_name = self.client._table_name(category)
        self._validate_metadata(parse_metadata(where))
        conditions, params = parse_conditions(where, where_document, ids)

        if limit is None:
            limit = 100  # or another default value
        if offset is None:
            offset = 0

        query = f"SELECT * FROM {table_name}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        self.client.cur.execute(query, tuple(params))

        rows = self.client.cur.fetchall()

        # Convert rows to list of dictionaries
        columns = [desc[0] for desc in self.client.cur.description]
        metadata_columns = [
            col for col in columns if col not in ["id", "document", "embedding"]
        ]

        result = []
        for row in rows:
            item = dict(zip(columns, row))
            metadata = {col: item[col] for col in metadata_columns}
            item["metadata"] = metadata
            result.append(item)

        output = {
            "ids": [row["id"] for row in result],
            "documents": [row["document"] for row in result],
            "metadatas": [row["metadata"] for row in result],
        }

        if len(result) == 0 or include is None:
            return output

        # embeddings is an array, check if include includes "embeddings"
        if 'embeddings' in include and result[0].get("embedding", None) is not None:
            output["embeddings"] = [row["embedding"] for row in result]
            # transform from ndarray to list
            output["embeddings"] = [emb.tolist() for emb in output["embeddings"]]

        if 'distances' in include and result[0].get("distance", None) is not None:
            output["distances"] = [row["distances"] for row in result]
            # transform to list
            output["distances"] = [dist.tolist() for dist in output["distances"]]

        return output

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
        return self.client.query(
            self.category, query_texts, n_results, where, where_document
        )

    def update(self, ids, documents=None, metadatas=None, embeddings=None):
        # if embeddings is not None
        if embeddings is None:
            if documents is None:
                documents = [None] * len(ids)
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
        conditions, params = parse_conditions(where, where_document, ids)

        if conditions:
            query = f"DELETE FROM {table_name} WHERE " + " AND ".join(conditions)
        else:
            raise Exception("No valid conditions provided for deletion.")

        self.client.cur.execute(query, tuple(params))
        self.client.connection.commit()


default_model_path = str(Path.home() / ".cache" / "onnx_models")


class PostgresClient(AgentMemory):
    def __init__(
        self,
        connection_string,
        model_name="all-MiniLM-L6-v2",
        model_path=default_model_path,
        embedding_width=384,
    ):
        self.connection = psycopg2.connect(connection_string)
        self.cur = self.connection.cursor()
        from pgvector.psycopg2 import register_vector

        register_vector(self.cur)  # Register PGVector functions
        full_model_path = check_model(model_name=model_name, model_path=model_path)
        self.model_path = full_model_path
        self.embedding_width = embedding_width
        self.collections = {}

    def _table_name(self, category):
        return f"memory_{category}"

    def ensure_table_exists(self, category):
        table_name = self._table_name(category)
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                document TEXT NOT NULL,
                embedding VECTOR({self.embedding_width})
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
            AgentCollection(name=row[0].split("_")[1])
            for row in self.cur.fetchall()
            if row[0].startswith("memory_")
        ]

    def get_collection(self, category, metadata=None):
        if collection := self.collections.get(category):
            if metadata:
                collection._validate_metadata(metadata)
        else:
            # Should we check for table existence here?
            collection = PostgresCollection(category, self, metadata)
        return collection

    def delete_collection(self, category):
        table_name = self._table_name(category)
        self.cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.connection.commit()
        self.collections.pop(category, None)

    def get_or_create_collection(self, category, metadata=None):
        if collection := self.collections.get(category):
            if metadata:
                collection._validate_metadata(metadata)
        else:
            collection = PostgresCollection(category, self, metadata)
        return collection

    def insert_memory(self, category, document, metadata={}, embedding=None, id=None):
        collection = self.get_or_create_collection(category, metadata)
        table_name = self._table_name(category)

        if embedding is None:
            embedding = self.create_embedding(document)

        # Extracting the keys and values from metadata to insert them into respective columns
        columns = ["document", "embedding"] + list(metadata.keys())
        placeholders = ["%s"] * len(columns)
        values = [document, embedding] + list(metadata.values())

        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})
        RETURNING id;
        """
        self.cur.execute(query, tuple(values))
        self.connection.commit()
        return self.cur.fetchone()[0]

    def create_embedding(self, document):
        embeddings = infer_embeddings([document], model_path=self.model_path)
        return embeddings[0]

    def add(self, category, documents, metadatas, ids):
        metadatas = list(metadatas)  # in case it's a consumable iterable
        meta_keys = reduce(set.union, (set(parse_metadata(m)) for m in metadatas), set())
        collection = self.get_or_create_collection(category, meta_keys)
        table_name = self._table_name(category)
        with self.connection.cursor() as cur:
            for document, metadata, id_ in zip(documents, metadatas, ids):
                columns = ["id", "document", "embedding"] + list(metadata.keys())
                placeholders = ["%s"] * len(columns)
                embedding = self.create_embedding(document)
                values = [id_, document, embedding] + list(metadata.values())

                query = f"""
                INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});
                """
                cur.execute(query, tuple(values))
            self.connection.commit()

    def query(
        self, category, query_texts, n_results=5, where=None, where_document=None
    ):
        collection = self.get_or_create_collection(category, parse_metadata(where))
        table_name = self._table_name(category)
        collection._validate_metadata(parse_metadata(where))
        conditions, params = parse_conditions(where, where_document)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        results = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "embeddings": [],
            "distances": [],
        }
        with self.connection.cursor() as cur:
            for emb in query_texts:
                query_emb = self.create_embedding(emb)
                params_with_emb = [query_emb] + params + [query_emb, n_results]
                string = f"""
                    SELECT id, document, embedding, embedding <-> %s AS distance, *
                    FROM {table_name}
                    {where_clause}
                    ORDER BY embedding <-> %s
                    LIMIT %s
                    """
                cur.execute(
                    string,
                    tuple(params_with_emb),
                )
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                metadata_columns = [
                    col
                    for col in columns
                    if col not in ["id", "document", "embedding", "distance"]
                ]
                for row in rows:
                    results["ids"].append(row[0])
                    results["documents"].append(row[1])
                    results["embeddings"].append(row[2])
                    results["distances"].append(row[3])
                    metadata = {
                        col: row[columns.index(col)] for col in metadata_columns
                    }
                    results["metadatas"].append(metadata)
        return results

    def update(self, category, id_, document=None, metadata=None, embedding=None):
        collection = self.get_or_create_collection(category, parse_metadata(metadata))
        table_name = self._table_name(category)
        with self.connection.cursor() as cur:
            if document:
                if embedding is None:
                    embedding = self.create_embedding(document)
                if metadata:
                    columns = ["document=%s", "embedding=%s"] + [
                        f"{key}=%s" for key in metadata.keys()
                    ]
                    values = [document, embedding] + list(metadata.values())
                else:
                    columns = ["document=%s", "embedding=%s"]
                    values = [document, embedding]

                query = f"""
                UPDATE {table_name}
                SET {', '.join(columns)}
                WHERE id=%s
                """
                cur.execute(query, tuple(values) + (id_,))
            elif metadata:
                collection._validate_metadata(metadata)
                columns = [f"{key}=%s" for key in metadata.keys()]
                values = list(metadata.values())
                query = f"""
                UPDATE {table_name}
                SET {', '.join(columns)}
                WHERE id=%s
                """
                cur.execute(query, tuple(values) + (id_,))
            self.connection.commit()

    def close(self):
        self.cur.close()
        self.connection.close()


def create_client():
    postgres_connection_string = os.environ.get("POSTGRES_CONNECTION_STRING")
    model_name = os.environ.get("POSTGRES_MODEL_NAME", "all-MiniLM-L6-v2")
    embedding_width = os.environ.get("EMBEDDING_WIDTH", 384)
    if postgres_connection_string is None:
        raise EnvironmentError(
            "Postgres connection string not set in environment variables!"
        )
    return PostgresClient(postgres_connection_string, model_name=model_name, embedding_width=embedding_width)

