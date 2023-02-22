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

    load_dotenv(override=True)
    db = os.getenv("DB_NAME", '')
    host = os.getenv("DB_HOST", '')
    user = os.getenv("DB_USER", '')
    pw = os.getenv("DB_PW", '')
    openai_api_key = os.getenv("OPENAI_API_KEY", '')
    
    tab1, tab2 = st.tabs(["Database Connection", "Model Playground"])
    with tab1:
        load_dotenv()
        db = os.getenv("DB_NAME", '')
        host = os.getenv("DB_HOST", '')
        user = os.getenv("DB_USER", '')
        pw = os.getenv("DB_PW", '')
        
        st.info("Enter database credentials")

        if "sql" not in st.session_state:
            st.session_state["sql"] = ""

        db_host = st.text_input("Enter host", value=host, placeholder="db.bit.io")
        db_user = st.text_input("Enter username", value=user, placeholder="postgres")
        db_password = st.text_input("Enter password", value=pw, type="password")
        db_name = st.text_input("Enter database name", value=db, placeholder="bitdotio/palmerpenguins")
        openai_key = st.text_input("Enter OpenAI Key", value=openai_api_key, type="password")
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
                    st.error("Error while trying to establish connection: {}".format(e))
            else:
                st.error(
                    "Connection failed. Please check your credentials and try again."
                )
            connection_pool.close()

    with tab2:
        with open('./example_schema.json', 'r') as f:
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
        st.markdown(
            """### initialization Prompt
        
        This represents the initial prompt supplied by the client.
    The user does not have access to this prompt. `{user_input}`
    will be replaced by the user's prompt in the final prompt."""
        )

        init_prompt = st.text_area(
            label="Enter initialization Prompt",
            value="-- A PostgreSQL query to return 1 and a PostgreSQL query for {user_input}\nSELECT 1;",
        )

        include_schema = st.checkbox("Include Schema Details", value=True)

        plain_text = st.text_area("Enter plain text query", value='How many penguins are there?')

        combined_prompt = init_prompt.replace("{user_input}", plain_text)
        prompt_schema = describe_database(json.loads(st.session_state.get("test_schema"))) if include_schema else ""
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
