import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'No2lonely*')
    MYSQL_DB = os.getenv('MYSQL_DB', 'ngo')
    MYSQL_PORT = os.getenv('MYSQL_PORT', 3306)