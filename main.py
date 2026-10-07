from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session
from typing import Annotated

from pydantic import BaseModel

import models
from models import Message_Table
from database import engine, Sessionlocal

import os
import smtplib

from dotenv import load_dotenv
from email.message import EmailMessage


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI()


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CREATE DATABASE TABLE
# =========================================================

models.Base.metadata.create_all(bind=engine)


# =========================================================
# PYDANTIC MODEL
# =========================================================

class CreateMessage(BaseModel):
    Name: str
    Email: str
    subject: str
    Phone: str
    message: str


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():
    db = Sessionlocal()

    try:
        yield db

    finally:
        db.close()


db_dependency = Annotated[
    Session,
    Depends(get_db)
]


# =========================================================
# SEND EMAIL FUNCTION
# =========================================================

def send_email(message_data: CreateMessage):

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise Exception(
            "EMAIL_ADDRESS or EMAIL_PASSWORD is missing in .env"
        )

    email = EmailMessage()

    # Email subject
    email["Subject"] = (
        f"Portfolio Contact: {message_data.subject}"
    )

    # Your Gmail
    email["From"] = EMAIL_ADDRESS

    # Email will come to your Gmail
    email["To"] = EMAIL_ADDRESS

    # When you click Reply, it will reply to visitor
    email["Reply-To"] = message_data.Email

    # Email body
    email.set_content(
        f"""
You received a new message from your portfolio website.

----------------------------------------
CONTACT INFORMATION
----------------------------------------

Name: {message_data.Name}

Email: {message_data.Email}

Phone: {message_data.Phone}

Subject: {message_data.subject}

----------------------------------------
MESSAGE
----------------------------------------

{message_data.message}

----------------------------------------

This message was sent from your portfolio contact form.
"""
    )

    # Connect to Gmail SMTP
    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        # Login
        smtp.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        # Send email
        smtp.send_message(email)


# =========================================================
# HOME ROUTE
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Portfolio Backend is running"
    }


# =========================================================
# CONTACT MESSAGE ROUTE
# =========================================================

@app.post("/message")
def create_message(
    message_class: CreateMessage,
    db: db_dependency
):

    # -----------------------------------------------------
    # SAVE MESSAGE TO DATABASE
    # -----------------------------------------------------

    message_model = Message_Table(
        **message_class.model_dump()
    )

    db.add(message_model)

    db.commit()

    db.refresh(message_model)


    # -----------------------------------------------------
    # SEND EMAIL
    # -----------------------------------------------------

    try:

        send_email(message_class)

        email_status = "Email sent successfully"

    except Exception as error:

        print("Email Error:", error)

        email_status = "Message saved, but email sending failed"


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return JSONResponse(
        status_code=201,

        content={
            "message": "Message submitted successfully",
            "email_status": email_status
        }
    )