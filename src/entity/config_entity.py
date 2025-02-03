import os
from constants import *
from dataclasses import dataclass
from datetime import datetime


TIMESTAMP: str = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

@dataclass
class SetUpConfig:
    database_name :  str = DATABASE_NAME
    model_name : str = MODEL_NAME
    langchain_tracing_v2 : str = LANGCHAIN_TRACING_V2
    langchain_api_key : str = LANGCHAIN_API_KEY
    openai_api_key : str = OPENAI_API_KEY

