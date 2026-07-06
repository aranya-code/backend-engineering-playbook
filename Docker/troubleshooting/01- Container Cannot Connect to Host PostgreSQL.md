# Container Cannot Connect to Host PostgreSQL

![Database Issue](../images/DB_Issue.png)

## Option 1 — Database Running on Your Windows Machine

If you already have PostgreSQL installed and running natively on your local computer, you just need to tell Docker how to reach outside the container and talk to your host machine.

Docker has a special DNS name specifically for this: `host.docker.internal`.

![Fix 1](../images/DB_Issue_Fix.png)

## Option 2 — Containerize the Database

![Fix 2](../images/DB_Containerize.png)

```yaml
services:
  web:
    build: .
    command: "python manage.py runserver 0.0.0.0:8000"
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DEBUG=1
    depends_on:
      - db # This tells Docker to start the DB first

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=my_database_name
      - POSTGRES_USER=my_database_user
      - POSTGRES_PASSWORD=my_secure_password
    ports:
      - "5432:5432"
```
