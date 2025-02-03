import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()

DATABASE_NAME : str = "sqlite:///patients.db" 
MODEL_NAME : str = "gpt-4o-mini"
os.chdir("../")
LANGCHAIN_TRACING_V2: str = "true"
LANGCHAIN_API_KEY : str = os.environ.get('LANGCHAIN_API_KEY')
OPENAI_API_KEY : str = os.environ.get('OPENAI_API_KEY')

