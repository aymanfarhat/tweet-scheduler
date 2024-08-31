"""Simple web server module built with fastapi"""
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# Load API key from .env file
load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def read_root(request: Request):
    """
    Renders and returns the content of the index.html file.

    Returns:
        str: The content of the index.html file.
    """
    return templates.TemplateResponse(
        request=request, name="index.html",
    )
