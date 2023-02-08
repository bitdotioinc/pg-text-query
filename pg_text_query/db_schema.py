"""Provides utilities for extracting structured schema data from a Postgres db."""

import itertools
import typing as t

import psycopg2


# Query includes schemas, tables, columns, and associated comments
GET_DB_SCHEMA_SQL = """
SELECT
    (SELECT pg_catalog.shobj_description(d.oid, 'pg_database')
    FROM   pg_catalog.pg_database d
    WHERE  datname = %s) AS "description",
    "information_schema"."schemata"."catalog_name" as "name",
    "information_schema"."schemata"."schema_name" as "schemata.name",
    "information_schema"."tables"."table_name" as "schemata.tables.name",
    "information_schema"."tables"."table_type" as "schemata.tables.type",
    "information_schema"."columns"."column_name" AS "schemata.tables.columns.name",
    "information_schema"."columns"."ordinal_position" AS "schemata.tables.columns.ordinal_position",
    "information_schema"."columns"."column_default" AS "schemata.tables.columns.column_default",
    "information_schema"."columns"."is_nullable" AS "schemata.tables.columns.is_nullable",
    "information_schema"."columns"."data_type" AS "schemata.tables.columns.data_type",
    "information_schema"."columns"."character_maximum_length" AS "schemata.tables.columns.character_maximum_length",
    obj_description(
        quote_ident("information_schema"."schemata"."schema_name")::regnamespace::oid,
        'pg_namespace'
    ) AS "schemata.description",
    -- NOTE: it is important to use the concat operator || and not the concat function below, as the former returns
    -- NULL if any component is NULL and avoids breaking obj_description with queries for the non-existent relation "."
    obj_description(
        (quote_ident("information_schema"."schemata"."schema_name") || '.' || quote_ident("information_schema"."tables"."table_name"))::regclass::oid,
        'pg_class'
    )  AS "schemata.tables.description",
    col_description(
        (quote_ident("information_schema"."schemata"."schema_name")  || '.' || quote_ident("information_schema"."tables"."table_name"))::regclass::oid,
        "information_schema"."columns"."ordinal_position"
    ) AS "schemata.tables.columns.description"
FROM "information_schema"."schemata"
LEFT JOIN "information_schema"."tables" ON "information_schema"."schemata"."schema_name" = "information_schema"."tables"."table_schema"
LEFT JOIN "information_schema"."columns" ON "information_schema"."tables"."table_name" = "information_schema"."columns"."table_name" AND "information_schema"."tables"."table_schema" = "information_schema"."columns"."table_schema"
WHERE "information_schema"."schemata"."schema_name" != 'pg_catalog'
AND "information_schema"."schemata"."schema_name" != 'information_schema'
AND "information_schema"."schemata"."schema_name" != 'pg_toast'
ORDER BY "schemata.name", "schemata.tables.name";
"""


def _get_column_index(cur: psycopg2._psycopg.cursor, column_name: str) -> int:
    for i, column in enumerate(cur.description):
        if column.name == column_name:
            return i
    return -1


class Relation(t.TypedDict):
    name: str
    description: t.Optional[str]
    columns: t.List[dict]


class Schema(t.TypedDict):
    name: str
    description: t.Optional[str]
    is_foreign: bool
    tables: t.List
    views: t.List


class InfoSchemaCache(t.TypedDict):
    name: str
    description: t.Optional[str]
    schemata: t.List[Schema]


def get_db_schema(cur: psycopg2._psycopg.cursor, db_name: str) -> InfoSchemaCache:
    """Extract structured schema data from an existing Postgres database.

    cur is a cursor from an open psycopg2 connection to the target database.
    """
    info_schema_dict: InfoSchemaCache = {
        "name": "",
        "description": None,
        "schemata": [],
    }
    cur.execute(GET_DB_SCHEMA_SQL, (db_name,))

    db_idx = _get_column_index(cur, "name")
    db_description_idx = _get_column_index(cur, "description")
    table_type_idx = _get_column_index(cur, "schemata.tables.type")
    table_comment_idx = _get_column_index(cur, "schemata.tables.description")
    schema_idx = _get_column_index(cur, "schemata.name")
    schema_comment_idx = _get_column_index(cur, "schemata.description")
    rel_idx = _get_column_index(cur, "schemata.tables.name")

    for i, (schema_name, schema_rows) in enumerate(
        itertools.groupby(cur.fetchall(), key=lambda row: row[schema_idx])
    ):
        schema: Schema = {
            "name": schema_name,
            "description": None,
            "is_foreign": False,
            "tables": [],
            "views": [],
        }
        for j, (rel_name, rel_rows) in enumerate(
            itertools.groupby(schema_rows, key=lambda row: row[rel_idx])
        ):
            rel: Relation = {"name": rel_name, "description": None, "columns": []}
            table_type: t.Optional[t.Literal["tables", "views"]] = None

            for k, row in enumerate(rel_rows):
                table_type = "views" if row[table_type_idx] == "VIEW" else "tables"
                if i == 0:
                    info_schema_dict["description"] = row[db_description_idx]
                    info_schema_dict["name"] = row[db_idx]
                if j == 0:
                    schema["description"] = row[schema_comment_idx]
                if k == 0:
                    rel["description"] = row[table_comment_idx]
                col = {}
                for column, value in zip(cur.description, row):
                    path = column.name.split(".")
                    if "columns" in path:
                        col[path[-1]] = value

                if col["name"] is not None:
                    rel["columns"].append(col)

            if rel["name"] and table_type:
                schema[table_type].append(rel)

        info_schema_dict["schemata"].append(schema)

    return info_schema_dict
