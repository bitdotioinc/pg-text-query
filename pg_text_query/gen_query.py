"""A trivial wrapper of openai.Completion.create (for now).

Handles initialization of a default request config with optional override by
config file and/or arbitrary kwargs to generate_query.py.
"""

import os
import typing as t

import openai
import yaml

from pg_text_query.errors import EnvVarError


# Initialize default OpenAI completion config w/ optional user config file path
# from ENV var PGTQ_OPENAI_CONFIG
PGTQ_OPENAI_CONFIG = os.getenv(
    "PGTQ_OPENAI_CONFIG",
    os.path.join(os.path.dirname(__file__), "default_openai_config.yaml"),
)
with open(PGTQ_OPENAI_CONFIG, "rb") as f:
    DEFAULT_COMPLETION_CONFIG = yaml.safe_load(f)["completion_create"]


def generate_query(prompt: str, **kwargs: t.Any) -> str:
    """Generate a raw Postgres query string from a prompt.
    
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


    response = openai.Completion.create(
        prompt=prompt,
        **{**DEFAULT_COMPLETION_CONFIG, **kwargs},
    )

    return response["choices"][0]["text"]

if __name__ == "__main__":
    print(DEFAULT_COMPLETION_CONFIG)