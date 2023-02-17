# db_connect.py
import psycopg
import psycopg_pool
import streamlit as st

#@st.cache_resource
def create_connection_pool(db_host, db_user, db_password, db_name):
    try:
        connection_string = f"host={db_host} user={db_user} password={db_password} dbname='{db_name}'"
        connection_pool = psycopg_pool.ConnectionPool(connection_string)
        return connection_pool
    except Exception as e:
        raise(e)
