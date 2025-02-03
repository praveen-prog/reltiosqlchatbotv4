import os
import logging

from from_root import from_root
from datetime import datetime 

LOG_FILE = f"{ datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
logs_dir = os.path.join(os.getcwd(),"logs")
logs_path = os.path.join(logs_dir , LOG_FILE)

os.makedirs(logs_dir, exist_ok=True)
LOG_FILE_PATH = os.path.join(logs_dir, LOG_FILE)

logging.basicConfig(
    filename = LOG_FILE_PATH,
    format = "[%(asctime)s] %(name)s - %(levelname)s - %(message)s" ,
    level = logging.DEBUG

)