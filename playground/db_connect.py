"""A module for creating and managing a connection pool for a PostgreSQL database.

This module uses the `psycopg-pool` package to create a connection pool, which allows for efficient reuse of
connections and reduces the overhead of creating new connections for each query. 

Example usage:
    connection_pool = create_connection_pool('localhost', 'postgres', 'password', 'example_db')
    connection = connection_pool.getconn()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM example_table')
    results = cursor.fetchall()
    connection_pool.putconn(connection)

Functions:
    create_connection_pool(db_host, db_user, db_password, db_name):
        Create a connection pool for the specified database.

        Args:
            db_host (str): The hostname or IP address of the database server.
            db_user (str): The username to use for connecting to the database.
            db_password (str): The password to use for connecting to the database.
            db_name (str): The name of the database to connect to.

        Returns:
            A `psycopg-pool` connection pool object.
"""

import psycopg_pool


def create_connection_pool(db_host, db_user, db_password, db_name):
    """Create a connection pool to a PostgreSQL database.

    Args:
        db_host (str): The hostname or IP address of the PostgreSQL server.
        db_user (str): The username to use for the connection.
        db_password (str): The password to use for the connection.
        db_name (str): The name of the database to connect to.

    Returns:
        ConnectionPool: A connection pool object that can be used to get database connections.

    Raises:
        Exception: If there is an error while creating the connection pool.

    """
    try:
        connection_string = f"host={db_host} user={db_user} password={db_password} dbname='{db_name}'"
        connection_pool = psycopg_pool.ConnectionPool(connection_string)
        return connection_pool
    except Exception as e:
        raise e
