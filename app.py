import os
from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import re

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_key")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Database Configuration
Base = declarative_base(metadata=MetaData())
engine = create_engine('sqlite:///miam_miam.db')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Request(Base):
    __tablename__ = 'requests'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    prompt = Column(String)
    response = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Prompts
RECIPE_PROMPT = """
You are a recipe generator.
The user will provide a list of ingredients.
You will generate a recipe using only those ingredients.
Do not include any conversational text.
Only provide the recipe.
"""

IMAGE_PROMPT = """
You are an image generator.
The user will provide a recipe.
You will generate a prompt for an image of the recipe.
The image should look amazing and make people want to eat it.
"""

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not validate_email(email):
            return render_template('register.html', error='Invalid email format')

        hashed_password = generate_password_hash(password)
        session_db = Session()
        new_user = User(email=email, password=hashed_password)
        session_db.add(new_user)
        session_db.commit()
        session_db.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        session_db = Session()
        user = session_db.query(User).filter_by(email=email).first()
        session_db.close()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_prompt = request.form['prompt']
        session_db = Session()
        user_id = session['user_id']
        
        # Save user request
        new_request = Request(user_id=user_id, prompt=user_prompt)
        session_db.add(new_request)
        session_db.commit()

        # Gemini Recipe Generation
        gemini_prompt = f"{RECIPE_PROMPT}\n{user_prompt}"
        response_stream = model.generate_content(gemini_prompt, stream=True)
        recipe_text = ""
        for chunk in response_stream:
            recipe_text += chunk.text
        
        # Save Gemini response
        new_request.response = recipe_text
        session_db.commit()

        # Gemini Image Generation
        image_prompt = f"{IMAGE_PROMPT}\n{recipe_text}"
        image_response = model.generate_content(image_prompt)

        image_prompt_response = model.generate_content(image_prompt)
        image_prompt_text = ""
        for chunk in image_prompt_response:
            image_prompt_text += chunk.text

        session_db.close()
        return render_template('home.html', recipe=recipe_text, image_prompt=image_prompt_text)
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
