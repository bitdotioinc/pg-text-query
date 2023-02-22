import sys
import os

sys.path.append("../pg_text_query/")
sys.path.append("../")
from db_schema import get_db_schema
from prompt import concat_prompt, describe_database
from gen_query import generate_query
import streamlit as st
import pandas as pd
from db_connect import create_connection_pool
import json
from dotenv import load_dotenv


def main():

    st.write("# Natural Language to SQL Translation Prompt Playground")
    load_dotenv(override=True)
    db = os.getenv("DB_NAME", "")
    host = os.getenv("DB_HOST", "")
    user = os.getenv("DB_USER", "")
    pw = os.getenv("DB_PW", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")

    tab1, tab2 = st.tabs(["API Key/Connection Details", "Model Playground"])
    with tab1:
        load_dotenv(override=True)
        db = os.getenv("DB_NAME", "")
        host = os.getenv("DB_HOST", "")
        user = os.getenv("DB_USER", "")
        pw = os.getenv("DB_PW", "")

        intro_text = """
Welcome to the text-to-sql prompt playground! To get started, get
        and enter your OpenAI API key below. You can learn about the OpenAI API [here](https://openai.com/api/).
        Additionally, if you'd like to try this out on a live PostgreSQL database, enter your database
        credentials below.

We recommend saving these values as environment variables. Fill out the `env_template` file
        with your OpenAI API key and database credentials and save it as `.env`, and these fields will
        be populated automatically."""

        st.info(intro_text)

        if "sql" not in st.session_state:
            st.session_state["sql"] = ""

        openai_key = st.text_input(
            "Enter OpenAI Key", value=openai_api_key, type="password"
        )
        db_host = st.text_input("Enter Postgres host", value=host, placeholder="db.bit.io")
        db_user = st.text_input("Enter Postgres Username", value=user, placeholder="postgres")
        db_password = st.text_input("Enter Postgres Password", value=pw, type="password")
        db_name = st.text_input(
            "Enter Postgres Database Name", value=db, placeholder="bitdotio/palmerpenguins"
        )
        # os.environ["OPENAI_API_KEY"] = openai_key

        if st.button("**Test Connection**"):
            connection_pool = create_connection_pool(
                db_host, db_user, db_password, db_name
            )
            if connection_pool:
                try:
                    connection = connection_pool.getconn()
                    cursor = connection.cursor()
                    cursor.execute("SELECT 1")
                    connection_pool.putconn(connection)
                    st.success("Connection successful!")
                except Exception as e:
                    st.error("Error while trying to establish connection: {}".format(e))
            else:
                st.error(
                    "Connection failed. Please check your credentials and try again."
                )
            connection_pool.close()

    with tab2:
        with open("./example_schema.json", "r") as f:
            example_schema = json.load(f)
        st.session_state["test_schema"] = json.dumps(example_schema)
        if st.button("Get Database Schema"):
            connection_pool = create_connection_pool(
                db_host, db_user, db_password, db_name
            )
            curs = connection_pool.getconn().cursor()
            st.session_state["schema_from_db"] = get_db_schema(curs, db_name)
            with st.expander("**Database Schema**"):
                test_schema = st.text_area(
                    "*Review and Edit Schema*",
                    value=json.dumps(st.session_state["schema_from_db"], indent=2),
                    key="test_schema",
                    height=900,
                )
        else:
            with st.expander("**Database Schema**"):
                test_schema = st.text_area(
                    "*Review and Edit Schema*",
                    value=st.session_state.get("test_schema", ""),
                    key="test_schema",
                    height=900,
                )
        st.info(
            """### Initialization Prompt

This represents the initial prompt supplied by the client.
    The end user does not have access to this prompt. `{user_input}`
    will be replaced by the user's prompt in the final prompt.

This prompt should specify the language (PostgreSQL) and any other instructions necessary
            to ensure the user's prompt, specified below, has the desired outcome."""
        )

        init_prompt = st.text_area(
            label="***Enter initialization Prompt***",
            value="-- A PostgreSQL query to return 1 and a PostgreSQL query for {user_input}\nSELECT 1;",
        )
        st.info(
            """### Schema Details
Check this box if you want details of the database schema (see above)
included in the prompt. Click the "Get Database Schema" button to get schema details from the connected database.
        Otherwise and example schema will be used."""
        )

        include_schema = st.checkbox("**Include Schema Details**", value=True)
        st.info(
            """### Plain Text Query
In the box below, provide a natural language
        statement of the desired database operation. This is what the end user would pass on for translation."""
        )

        plain_text = st.text_area(
            "***Enter plain text query***", value="How many penguins are there?"
        )

        st.info(
            """### Final Prompt
This is the final prompt sent to the OpenAI API. It is generated automatically from the fields above. You
        can make final edits before sending if needed."""
        )

        combined_prompt = init_prompt.replace("{user_input}", plain_text)
        prompt_schema = (
            describe_database(json.loads(st.session_state.get("test_schema")))
            if include_schema
            else ""
        )
        prompt_to_send = st.text_area(
            label="Prompt to Send",
            value=concat_prompt(
                f"-- Language PostgreSQL",
                prompt_schema,
                combined_prompt,
            ),
            height=450,
        )

        if st.button("Generate SQL"):
            st.session_state["sql"] = generate_query(prompt_to_send)
        st.code(st.session_state["sql"], language="sql")

        if st.button("Run SQL"):
            # connect to the database using the provided credentials
            # and execute the generated SQL code
            connection_pool = create_connection_pool(
                db_host, db_user, db_password, db_name
            )

            if connection_pool:
                connection = connection_pool.getconn()
                cursor = connection.cursor()
                cursor.execute(st.session_state["sql"])
                st.code(cursor.fetchmany(50))


if __name__ == "__main__":
    main()
