"""
pip install psycopg # psycopg-3.1.8-py3-none-any.whl

# turns on postgres and materialize server, we've done the connection via docker compose
docker compose up -d src/metrics/docker-compose.yml

# turns off postgres and materialize server
docker compose down src/metrics/docker-compose.yml
"""

import sys

import psycopg

# Establish connection to Postgres server
conn = psycopg.connect(
    dbname="my_db",
    user="user",
    password="pass",
    host="localhost",
    port="5432",
)
conn.autocommit = True

# Create a cursor to interact with the database
cur = conn.cursor()

# Execute a SQL command to show the wal_level setting
cur.execute("SHOW wal_level")

# Fetch the result
result = cur.fetchone()

# Print the result
print(f"wal_level: {result[0]}")

# Close the cursor and connection
cur.close()
conn.close()
