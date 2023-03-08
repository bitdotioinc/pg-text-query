"""A Streamlit app for generating SQL queries from natural language prompts using OpenAI's GPT-3
   language model."""

import os
import sys
import json

import streamlit as st
from dotenv import load_dotenv

from db_connect import create_connection_pool
# Get the absolute path of the parent directory
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dirname = os.path.dirname(__file__)

# Add the parent directory to the system path
sys.path.append(parent_dir)

from pg_text_query.db_schema import get_db_schema
from pg_text_query.gen_query import generate_query, generate_query_chat
from pg_text_query.prompt import concat_prompt, describe_database


def main():
    """streamlit app for generating SQL queries from natural language prompts
       and database schema information"""
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

        # Update the database connection variables with the user's input
        if db_name != db:
            db = db_name
        if db_host != host:
            host = db_host
        if db_user != user:
            user = db_user
        if db_password != pw:
            pw = db_password

        os.environ["OPENAI_API_KEY"] = openai_key

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
                    st.error(f"Error while trying to establish connection: {e}")
            else:
                st.error(
                    "Connection failed. Please check your credentials and try again."
                )
            connection_pool.close()

    with tab2:

        st.session_state["model_choice"] = st.radio(
            "Choose Model",
            ('Codex', 'ChatGPT'))

        st.write(
            """### Initialization Prompt

*This represents the initial prompt supplied by the client.
    The end user does not have access to this prompt. `{user_input}`
    will be replaced by the user's prompt in the final prompt.*

*This prompt should specify the language (PostgreSQL) and any other instructions necessary
            to ensure the user's prompt, specified below, has the desired outcome.*"""
        )

        if st.session_state["model_choice"] == "Codex":
            default_init_prompt = "-- A PostgreSQL query to return 1 and a PostgreSQL query for {user_input}\nSELECT 1;"
        elif st.session_state["model_choice"] == "ChatGPT":
            default_init_prompt = """You are a SQL code translator. Your role is to translate natural language to PostgreSQL. Your only output should be SQL code. Do not include any other text. Only SQL code.
Translate \"{user_input}\" to a syntactically-correct PostgreSQL query."""

        init_prompt = st.text_area(
            label="***Enter initialization Prompt***",
            value=default_init_prompt,
        )
        st.write(
            """### Schema Details
*Check this box if you want details of the database schema (see above)
included in the prompt. Click the "Get Database Schema" button to get schema
        details from the connected database.
        Otherwise and example schema will be used.*"""
        )

        include_schema = st.checkbox("**Include Schema Details**", value=True)

        if include_schema:

            if st.button("Get Database Schema"):
                connection_pool = create_connection_pool(
                    db_host, db_user, db_password, db_name
                )
                curs = connection_pool.getconn().cursor()
                schema_from_db = get_db_schema(curs, db_name)
                st.session_state["test_schema"] = json.dumps(schema_from_db, indent=2)  # Update test_schema value
            elif not st.session_state.get("test_schema"):
                with open(os.path.join(dirname, "example_schema.json"), "r") as f:
                    example_schema = json.load(f)
                st.session_state["test_schema"] = json.dumps(example_schema, indent=2)

            with st.expander("**Database Schema**"):
                schema_text_area = st.text_area(
                    "*Review and Edit Schema*",
                    value=st.session_state["test_schema"],
                    height=900,
                )
            # Save schema shown to a variable accessible elsewhere in the app
            st.session_state["test_schema"] = schema_text_area

        st.write(
            """### Plain Text Query
*In the box below, provide a natural language
        statement of the desired database operation. This is what the end user would pass on for translation.*"""
        )

        plain_text = st.text_area(
            "***Enter plain text query***", value="How many penguins are there?"
        )

        st.write(
            """### Final Prompt
*This is the final prompt sent to the OpenAI API. It is generated automatically from the fields above. You
        can make final edits before sending if needed.*"""
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
                "-- Language PostgreSQL",
                prompt_schema,
                combined_prompt,
            ),
            height=250,
        )


        if st.button("Generate SQL"):
            if st.session_state["model_choice"] == "Codex":
                st.session_state["sql"] = generate_query(prompt_to_send)
            elif st.session_state["model_choice"] == "ChatGPT":
                st.session_state["sql"] = generate_query_chat(prompt_to_send,
                                                              system=None)
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
