"""A trivial wrapper of openai.Completion.create (for now).

Handles initialization of a default request config with optional override by
config file and/or arbitrary kwargs to generate_query.py.
"""

import os
import typing as t

import openai
import yaml
from pglast.parser import parse_sql, ParseError

from pg_text_query.errors import EnvVarError, QueryGenError


# Initialize default OpenAI completion config w/ optional user config file path
# from env var PGTQ_OPENAI_CONFIG
PGTQ_OPENAI_CONFIG = os.getenv(
    "PGTQ_OPENAI_CONFIG",
    os.path.join(os.path.dirname(__file__), "default_openai_config.yaml"),
)
with open(PGTQ_OPENAI_CONFIG, "rb") as f:
    DEFAULT_COMPLETION_CONFIG = yaml.safe_load(f)["completion_create"]

CHAT_OPENAI_CONFIG = os.getenv(
    "CHAT_OPENAI_CONFIG",
    os.path.join(os.path.dirname(__file__), "openai_chat_config.yaml"),
    )

with open(CHAT_OPENAI_CONFIG, "rb") as f:
    CHAT_COMPLETION_CONFIG = yaml.safe_load(f)["completion_create"]



def generate_query(prompt: str, validate_sql: bool = False,
                   completion_type: str = "single", **kwargs: t.Any) -> str:
    """Generate a raw Postgres query string from a prompt.

    If validate_sql is True, raises QueryGenError when OpenAI returns a 
    completion that fails validation using the Postgres parser. This ensures a
    non-empty and syntactically valid query but NOT necessarily a correct one.
    
    Completion.create is called with default config from PGTQ_OPENAI_CONFIG
    with any provided kwargs serving as parameter overrides. 

    TODO: Later, add error handling.
    """
    # 
    if getattr(openai, "api_key") is None:
        # Initialize OpenAI API Key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if openai.api_key is None:
            raise EnvVarError("OPENAI_API_KEY not found in environment")

    if completion_type=="single":
        response = openai.Completion.create(
            prompt=prompt,
            **{**DEFAULT_COMPLETION_CONFIG, **kwargs},
        )

        generated_query = response["choices"][0]["text"]
        
    elif completion_type=="chat":
        system = kwargs.get("task_prompt", {}).get("system", None)
        if not system:
            system = "you are a text-to-SQL translator. You write PostgreSQL code based on plain-language prompts."

        query = [{"role":"system", "content": system}, {"role":"user", "content": prompt}]

        response = openai.ChatCompletion.create(
            messages=query,
            **{**CHAT_COMPLETION_CONFIG, **kwargs},
        )

        generated_query = response["choices"][0]["message"]["content"]
    else:
        raise ValueError("Must specify 'single' or 'chat' completion type")

    if validate_sql:
        if not is_valid_query(generated_query):
            raise QueryGenError("Generated query is empty, only a comment, or invalid.")
    
    return generated_query


def generate_query_chat(prompt: str, validate_sql: bool = False, system: t.Optional[str] = None, **kwargs: t.Any) -> str:
    """Generate a raw Postgres query string from a prompt using ChatGTP.

    If validate_sql is True, raises QueryGenError when OpenAI returns a 
    completion that fails validation using the Postgres parser. This ensures a
    non-empty and syntactically valid query but NOT necessarily a correct one.
    
    Completion.create is called with default config from PGTQ_OPENAI_CONFIG
    with any provided kwargs serving as parameter overrides. 

    TODO: Later, add error handling.
    """
    # 
    if getattr(openai, "api_key") is None:
        # Initialize OpenAI API Key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if openai.api_key is None:
            raise EnvVarError("OPENAI_API_KEY not found in environment")

    if not system:
        system = "you are a text-to-SQL translator. You write PostgreSQL code based on plain-language prompts."

    query = [{"role":"system", "content": system}, {"role":"user", "content": prompt}]

    response = openai.ChatCompletion.create(
        messages=query,
        **{**CHAT_COMPLETION_CONFIG, **kwargs},
    )

    generated_query = response["choices"][0]["message"]["content"]


    if validate_sql:
        if not is_valid_query(generated_query):
            raise QueryGenError("Generated query is empty, only a comment, or invalid.")
    
    return generated_query


def is_valid_query(query: str) -> bool:
    """Validates query syntax using Postgres parser.
    
    Note: in this context, "invalid" includes a query that is empty or only a
    SQL comment, which is different from the typical sense of "valid Postgres".
    """
    parse_result = None
    valid = True
    try:
        parse_result = parse_sql(query)
    except ParseError as e:
        valid = False
    # Check for any empty result (occurs if completion is empty or a comment)
    return parse_result and valid
