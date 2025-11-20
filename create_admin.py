from database_connector import DatabaseConnector

def create_admin_user():
    db = DatabaseConnector()
    connection = db.get_connection()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Create admin table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default admin user (password: admin123)
            cursor.execute("""
                INSERT IGNORE INTO admin_users (username, password_hash, email) 
                VALUES ('admin', 'pbkdf2:sha256:260000$admin123$hash_here', 'admin@ngo.org')
            """)
            
            connection.commit()
            print("Admin user created successfully!")
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
        finally:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_admin_user()