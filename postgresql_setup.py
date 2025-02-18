#!/usr/bin/env python3
import os
import subprocess
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(dotenv_path='.env', override=False)

POSTGRES_VERSION = os.getenv("POSTGRES_VERSION", "17")
DB_NAME = os.getenv("DBNAME")
DB_USER = os.getenv("DBUSER")
DB_PASSWORD = os.getenv("DBPASSWORD")
DB_HOST = os.getenv("DBHOST", "localhost")
DB_PORT = os.getenv("DBPORT", "5432")


def configure_postgresql():

    DB_NAME = os.getenv("DBNAME")
    DB_USER = os.getenv("DBUSER")
    DB_PASSWORD = os.getenv("DBPASSWORD")
    POSTGRES_VERSION = os.getenv("POSTGRES_VERSION")

    print("Configuring PostgreSQL...")

    try:
        # Step 1: Update pg_hba.conf to replace peer with md5
        pg_hba_path = f"/etc/postgresql/{POSTGRES_VERSION}/main/pg_hba.conf"
        update_pg_hba_command = f"""
sudo sed -i -e '/^local\\s\\+all\\s\\+all\\s\\+peer/s/peer/md5/' \\
            -e '/^host\\s\\+all\\s\\+all\\s\\+127.0.0.1\\/32\\s\\+peer/s/peer/md5/' \\
            -e '/^host\\s\\+all\\s\\+all\\s\\+::1\\/128\\s\\+peer/s/peer/md5/' {pg_hba_path}
"""
        subprocess.run(update_pg_hba_command, shell=True, check=True)
        print("pg_hba.conf updated for md5 authentication.")

        # Restart PostgreSQL to apply changes
        subprocess.run(["sudo", "systemctl", "restart", "postgresql"], check=True) # `systemctl` way
        #subprocess.run(["sudo", "service", "postgresql", "restart"], check=True) # `service` way for `WSL2`
        print("PostgreSQL service restarted successfully.")

        # Create database, user, and enable pgvector extension
        # Create the database if it doesn't exist
        subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "bash",
                "-c",
                f"if ! psql -lqt | cut -d '|' -f 1 | grep -qw {DB_NAME}; then "
                f"createdb {DB_NAME}; "
                f"echo 'Database {DB_NAME} created successfully.'; "
                f"else "
                f"echo 'Database {DB_NAME} already exists.'; "
                f"fi",
            ],
            check=True,
        )

        # Create the role if it doesn't exist
        subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "bash",
                "-c",
                f"if ! psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='{DB_USER}';\" | grep -qw 1; then "
                f"psql -c \"CREATE ROLE {DB_USER} WITH LOGIN PASSWORD '{DB_PASSWORD}';\"; "
                f"echo 'Role {DB_USER} created successfully.'; "
                f"else "
                f"echo 'Role {DB_USER} already exists.'; "
                f"fi",
            ],
            check=True,
        )

        # Configure the role
        subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "bash",
                "-c",
                f"psql -c \"ALTER ROLE {DB_USER} WITH SUPERUSER;\"; "
                f"psql -c \"ALTER ROLE {DB_USER} SET client_encoding TO 'utf8';\"; "
                f"psql -c \"ALTER ROLE {DB_USER} SET default_transaction_isolation TO 'read committed';\"; "
                f"psql -c \"ALTER ROLE {DB_USER} SET timezone TO 'UTC';\"; "
                f"echo 'Role {DB_USER} configured successfully.';",
            ],
            check=True,
        )

        # Grant privileges to the user on the database
        subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "bash",
                "-c",
                f"psql -c \"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};\"",
            ],
            check=True,
        )

        # Enable pgvector extension
        subprocess.run(
            [
                "sudo",
                "-u",
                "postgres",
                "bash",
                "-c",
                f"if ! psql -d {DB_NAME} -tAc \"SELECT 1 FROM pg_extension WHERE extname='vector';\" | grep -qw 1; then "
                f"psql -d {DB_NAME} -c \"CREATE EXTENSION vector;\"; "
                f"echo 'pgvector extension enabled for database {DB_NAME}.'; "
                f"else "
                f"echo 'pgvector extension is already enabled for database {DB_NAME}.'; "
                f"fi",
            ],
            check=True,
        )

        print(f"PostgreSQL configured successfully with database '{DB_NAME}', user '{DB_USER}', and 'pgvector' extension enabled.")

    except subprocess.CalledProcessError as e:
        print(f"Error configuring PostgreSQL: {e}")


configure_postgresql()
