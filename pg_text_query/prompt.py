"""prompt.py provides helpers for preparing Postgres query prompts."""

import typing as t


def get_default_prompt(
    text: str,
    db_schema: t.Dict[t.Any, t.Any],
    include_types: bool = True,
) -> str:
    """Construct a Postgres query prompt from natural text and a db schema.
    
    See pg_text_query.db_schema.py for the expected schema data format and a
    utility for extracting schema data in that format from an existing Postgres
    database.

    The prompt requests and provides an arbitrary "SELECT 1" query, in addition
    to the actual text request. This is a naive, baseline approach that has 
    been useful for hinting to the model that we want a raw SQL completion, as
    opposed to more SQL comments.

    This default prompt is provided for convenience, use concat_prompt and 
    describe_database to build custom prompts.
    """
    return concat_prompt(
        f"-- Language PostgreSQL",
        describe_database(db_schema, include_types),
        f"-- A PostgreSQL query to return 1 and a PostgreSQL query for {text}",
        "SELECT 1;",
    )

def get_custom_prompt(
        task_prompt: str,
        user_prompt: str,
        db_schema: t.Dict[t.Any, t.Any],
        include_schema: bool = True,
        include_types: bool = True,
        add_select_1: bool = True,
        ) -> str:
    """construct a Postgres query prompt from a task prompt, user prompt, and db schema.

    See pg_text_query.db_schema.py for the expected schema data format and a
    utility for extracting schema data in that format from an existing Postgres
    database.

    All prompts currently start with "--Language PostgreSQL" and the schema, if
    included, follows this language specification line.

    Include a space or newline at the end of task_prompt depending on whether you want
    the user_prompt on a new line.
    """
    task_user_prompt = task_prompt + user_prompt
    
    prompt_components = ["-- Language PostgreSQL\n",
                         describe_database(db_schema, include_types) if include_schema else '',
                         task_user_prompt,
                         ]
    if add_select_1:
        prompt_components.append("SELECT 1;")
    
    return concat_prompt(*prompt_components)

        


def concat_prompt(*args: str) -> str:
    return "\n".join(args)


def _describe_cols(cols: t.List[t.Dict[t.Any, t.Any]], include_types: bool) -> str:
    return ", ".join(
        [f"{c['name']}{' ' + c['data_type'] if include_types else ''}" for c in cols]
    )


def _describe_table(schema_name: str, table_name: str) -> str:
    return f'"{table_name}"' if schema_name == "public" else f'"{schema_name}"."{table_name}"'


def _describe_schema(schema: t.Dict[t.Any, t.Any], include_types: bool = True) -> str:
    return "\n".join(
        [
            f"-- Table = {_describe_table(schema['name'], t['name'])}, columns = [{_describe_cols(t['columns'], include_types)}]"
            for t in schema["tables"]
        ]
    )


def describe_database(
    db_schema: t.Dict[t.Any, t.Any], include_types: bool = True
) -> str:
    """Describes a database schema with SQL comments per Codex docs example.
    
    Ref: https://platform.openai.com/docs/guides/code/best-practices
    """
    return "\n".join(
        [
            _describe_schema(s, include_types=include_types)
            for s in db_schema["schemata"]
        ]
    )
