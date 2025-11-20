import mysql.connector
from config import Config

class DatabaseConnector:
    def __init__(self):
        self.config = Config()
    
    def get_connection(self):
        try:
            connection = mysql.connector.connect(
                host=self.config.MYSQL_HOST,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DB,
                port=self.config.MYSQL_PORT
            )
            return connection
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def execute_query(self, query, params=None):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params or ())
                result = cursor.fetchall()
                cursor.close()
                connection.close()
                return result
            except mysql.connector.Error as e:
                print(f"Error executing query: {e}")
                return None
        return None
    
    def execute_insert(self, query, params=None):
        connection = self.get_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(query, params or ())
                connection.commit()
                last_id = cursor.lastrowid
                cursor.close()
                connection.close()
                return last_id
            except mysql.connector.Error as e:
                print(f"Error executing insert: {e}")
                connection.rollback()
                return None
        return None