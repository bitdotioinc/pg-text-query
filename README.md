# pg-text-query
Utilities for generating and testing Postgres queries from natural text.

## TODO:
- code review
- `setup.py`
- prompt-engineering test approach/examples

# Example usage

## Structured Postgres schema extraction

```python
import os
from pprint import pprint

import bitdotio
from dotenv import load_dotenv

from pg_text_query import get_db_schema, get_default_prompt, generate_query

# Initialize OPENAI_API_KEY and BITIO_KEY
load_dotenv()


DB_NAME = "bitdotio/palmerpenguins"

b = bitdotio.bitdotio(os.getenv("BITIO_KEY"))

# Extract a structured db schema from Postgres
with b.pooled_cursor(DB_NAME) as cur:
    db_schema = get_db_schema(cur, DB_NAME)
pprint(db_schema)
```

Output:

```python
{
    "description": "# Palmer\xa0Archipelago (Antarctica) penguin data\n"
    "\n"
    "\n"
    ">\xa0The goal of palmerpenguins is to provide a great dataset "
    "for data exploration & visualization, as an alternative to "
    "`iris`.\n"
    "\n"
    "\n"
    "\\- "
    "[source](https://github.com/allisonhorst/palmerpenguins/)\n"
    "name": "bitdotio/palmerpenguins",
    "schemata": [
        {
            "description": "standard public schema",
            "is_foreign": False,
            "name": "public",
            "tables": [
                {
                    "columns": [
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "text",
                            "description": "penguin species "
                            "(Adélie, Chinstrap, "
                            "or\xa0Gentoo)",
                            "is_nullable": "YES",
                            "name": "species",
                            "ordinal_position": 2,
                        },
...TRUNCATED...
                        {
                            "character_maximum_length": None,
                            "column_default": None,
                            "data_type": "bigint",
                            "description": "study year (2007, " "2008, or 2007)",
                            "is_nullable": "YES",
                            "name": "year",
                            "ordinal_position": 9,
                        },
                    ],
                    "description": "Measurements of 344 penguins of "
                    "three different species from three "
                    "islands in the Palmer archipelago.",
                    "name": "penguins",
                }
            ],
            "views": [],
        }
    ],
}
```

## Prompt generation
```python
# Construct a prompt that includes text description of query
prompt = get_default_prompt(
    "most common species and island for each island",
    db_schema,
)
# Note: prompt includes extra `SELECT 1` as a naive approach to hinting for
# raw SQL continuation
print(prompt)
```

Output (prompt includes extra `SELECT 1` query as a naive approach to hinting for
    # raw SQL continuation):

```shell
-- Language PostgreSQL
-- Table penguins, columns = [species text, island text, bill_length_mm double precision, bill_depth_mm double precision, flipper_length_mm bigint, body_mass_g bigint, sex text, year bigint]
-- A PostgreSQL query to return 1 and a PostgreSQL query for most common species and island for each island
SELECT 1;
```

## Query generation
```python
# Using default OpenAI request config, which can be overriden here w/ kwargs
query = generate_query(prompt)
print(query)
```

Output: 

```shell
SELECT species, island, COUNT(*) FROM penguins GROUP BY species, island
```
