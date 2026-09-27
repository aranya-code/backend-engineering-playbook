import os
import pytest
import psycopg
import redis

@pytest.mark.integration
def test_postgres_connection():
    conn = psycopg.connect(
        dbname=os.getenv("POSTGRES_DB", "ci_db"),
        user=os.getenv("POSTGRES_USER", "ci_user"),
        password=os.getenv("POSTGRES_PASSWORD", "ci_password"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
    conn.close()

@pytest.mark.integration
def test_redis_connection():
    client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
    client.set("ci-key", "ok")
    assert client.get("ci-key") == b"ok"
