import os
from pprint import pprint

import bitdotio
from dotenv import load_dotenv

from pg_text_query import get_db_schema, get_default_prompt, generate_query

# Initialize OPENAI_API_KEY and BITIO_KEY
load_dotenv()


DB_NAME = "bitdotio/palmerpenguins"


def main():
    b = bitdotio.bitdotio(os.getenv("BITIO_KEY"))

    # Extract a structured db schema from Postgres
    with b.pooled_cursor(DB_NAME) as cur:
        db_schema = get_db_schema(cur, DB_NAME)
    print("Got structured db_schema:")
    pprint(db_schema)

    # Construct a prompt that includes text description of query
    prompt = get_default_prompt(
        "most common species and island for each island",
        db_schema,
    )
    # Note: prompt includes extra `SELECT 1` as a naive approach to hinting for
    # raw SQL continuation
    print(f"\nGenerated prompt:\n{prompt}")

    
    # Using default OpenAI request config, which can be overriden here w/ kwargs
    query = generate_query(prompt)
    print(f"Generated query:\n{query}\n")

    # Test the query against the database
    # USE CAUTION running unreviewed queries if your connection has write access
    with b.pooled_cursor(DB_NAME) as cur:
        cur.execute(query)
        print(f"Result: {cur.fetchall()}")
    

if __name__ == "__main__":
    main()