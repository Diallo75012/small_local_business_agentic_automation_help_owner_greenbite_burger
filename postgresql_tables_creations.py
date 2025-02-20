'''
File that create the database using postgresql python library ORM
like in django just use models to abstract away the database schema
source: `https://pypi.org/project/flask-pgsql/`
'''
import os
from flask_postgresql import PostgreSQL
from dotenv import load_dotenv


# load env vars
load_dotenv(dotenv_path='.env', override=False)

# Retrieve database connection parameters from environment variables
hostname = os.getenv("DBHOST")
port = int(os.getenv("DBPORT"))
database = os.getenv("DBNAME")
username = os.getenv("DBUSER")
password = os.getenv("DBPASSWORD")

# Initialize the PostgreSQL connection and to be imported by other part of code tomage a db connection
db = PostgreSQL(hostname=hostname, port=port, database=database, username=username, password=password)

# models
class Messages(db.Model):
  '''
    This will receive the messages that are randomly collected
  '''
  id = db.Column(db.Integer, primary_key=True)
  # index from dataframe so next agent can use same logic from database rows and just use same `.var.env` var to know where to start
  dfidx = db.Column(db.Integer, nullable=False)
  date = db.Column(db.Timestamp, nullable=False) # if issue with DateTime just use `String(50)`
  message = db.Column(db.String(500), nullable=False)

class Orders(db.Model):
  '''
    This will be validated orders after agent filtering through
  '''
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(db.Timestamp, nullable=False)
  message = db.Column(db.String(500), nullable=False) # Text/Structured data, e.g. JSON (Dumps) with extracted items

class Enquiries(db.Model):
  '''
    This will be what looks like an order but it is actually an enquire
  '''
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(db.Timestamp, nullable=False)
  message = db.Column(db.String(500), nullable=False) # enquiry_details (Text/structured data)

class MenuItems(db.Model):
  '''
    This table stores each menu item with detailed attributes. and will be put to cache later on.
    Client's DEV can change here the database following menu changes
  '''
  id = db.Column(db.Integer, primary_key=True)
  item_name = db.Column(db.String(30), nullable=False) # key in k/v cache
  description = db.Column(db.String(500), nullable=False) # value in k/v cache
  price = db.Column(db.Integer, unique=False, nullable=False) # value in k/v cache (with separator)

# create all tables (run it once at the beginning of the project then comment it out)
# db.create_all()
