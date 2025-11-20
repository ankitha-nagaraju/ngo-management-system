# simple_hero_image.py
import mysql.connector

try:
    # Use the same credentials as your Flask app
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='No2lonely*',  # Your actual MySQL password - if empty, keep as empty string
        database='ngo'
    )
    
    cursor = connection.cursor()

    # Read the image file
    print("📖 Reading image file...")
    with open(r'C:\Users\NIDHI NAGARAJU\Downloads\Education-in-india-1024x606-1.jpg', 'rb') as file:
        image_data = file.read()
    
    print(f"📊 Image file size: {len(image_data)} bytes")

    # Clear and insert
    print("💾 Saving to database...")
    cursor.execute("DELETE FROM website_settings")
    cursor.execute("INSERT INTO website_settings (id, hero_image) VALUES (1, %s)", (image_data,))
    connection.commit()

    # Verify
    cursor.execute("SELECT LENGTH(hero_image) FROM website_settings")
    result = cursor.fetchone()
    print(f"✅ Image size in database: {result[0]} bytes")

    cursor.close()
    connection.close()
    print("🎉 Hero image added successfully!")

except Exception as e:
    print(f"❌ Error: {e}")