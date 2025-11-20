from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv
import base64

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'ngo'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

# Test database connection
def test_db_connection():
    connection = get_db_connection()
    if connection:
        print("✅ Database connected successfully!")
        connection.close()
        return True
    else:
        print("❌ Database connection failed!")
        return False

# Public Routes
@app.route('/')
def home():
    connection = get_db_connection()
    hero_image = None
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT hero_image FROM website_settings WHERE id = 1")
            result = cursor.fetchone()
            if result and result['hero_image']:
                hero_image = result['hero_image']
                print(f"✅ Hero image found! Size: {len(hero_image)} bytes")
                
                # Convert to base64 for the template
                hero_image = base64.b64encode(hero_image).decode('utf-8')
                print(f"✅ Base64 conversion successful! Length: {len(hero_image)}")
            else:
                print("❌ No hero image found in database")
        except Exception as e:
            print(f"❌ Error fetching hero image: {e}")
        finally:
            cursor.close()
            connection.close()
    
    return render_template('public/home.html', hero_image=hero_image)

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        ngo_id = request.form['ngo_id']
        amount = request.form['amount']
        payment_method = request.form['payment_method']
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error. Please try again.', 'error')
            return redirect(url_for('donate'))
        
        cursor = connection.cursor()
        
        try:
            # Check if donor exists
            cursor.execute("SELECT Donor_id FROM donor WHERE Name = %s", (name,))
            donor = cursor.fetchone()
            
            if donor:
                donor_id = donor[0]
                cursor.execute("UPDATE donor SET Address = %s WHERE Donor_id = %s", (address, donor_id))
            else:
                cursor.execute("INSERT INTO donor (Name, Address) VALUES (%s, %s)", (name, address))
                donor_id = cursor.lastrowid
            
            if phone:
                cursor.execute("INSERT IGNORE INTO donor_phone (Donor_id, Phone) VALUES (%s, %s)", (donor_id, phone))
            
            if email:
                cursor.execute("INSERT IGNORE INTO donor_email (Donor_id, Email) VALUES (%s, %s)", (donor_id, email))
            
            cursor.execute("""
                INSERT INTO donation (Donor_id, Ngo_id, Amount, Donation_date, Payment_method) 
                VALUES (%s, %s, %s, CURDATE(), %s)
            """, (donor_id, ngo_id, amount, payment_method))
            
            connection.commit()
            flash('Thank you for your donation! Your support makes a difference.', 'success')
            return redirect(url_for('donation_success'))
            
        except Exception as e:
            connection.rollback()
            flash(f'Error processing donation: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error. Please try again.', 'error')
        return render_template('public/donate.html', ngos=[])
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT Ngo_id, Ngo_name FROM ngo")
    ngos = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('public/donate.html', ngos=ngos)

@app.route('/donation/success')
def donation_success():
    return render_template('public/donation_success.html')

@app.route('/events')
def public_events():
    connection = get_db_connection()
    if not connection:
        return render_template('public/events.html', events=[])
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, ngo.Ngo_name 
        FROM event e 
        JOIN ngo ON e.Ngo_id = ngo.Ngo_id 
        WHERE e.Event_date >= CURDATE() 
        ORDER BY e.Event_date ASC
    """)
    events = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('public/events.html', events=events)

@app.route('/ngos')
def public_ngos():
    connection = get_db_connection()
    if not connection:
        return render_template('public/ngos.html', ngos=[])
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT n.*, 
                   CalculateNgoEfficiency(n.Ngo_id) as Efficiency_Score
            FROM ngo n
        """)
        ngos = cursor.fetchall()
        
    except Exception as e:
        print(f"Error loading NGOs: {str(e)}")
        ngos = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('public/ngos.html', ngos=ngos)

@app.route('/about')
def about():
    return render_template('public/about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('public/contact.html')

# Volunteer Routes
@app.route('/volunteers')
def public_volunteers():
    # This just renders the volunteer registration form
    return render_template('public/volunteers.html')

@app.route('/volunteer/register', methods=['GET', 'POST'])
def volunteer_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        skills = request.form.getlist('skills')  # Multiple skills
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error. Please try again.', 'error')
            return redirect(url_for('volunteer_register'))
        
        cursor = connection.cursor()
        
        try:
            # Check if volunteer already exists with this email
            cursor.execute("""
                SELECT v.Volunteer_id 
                FROM volunteer v
                JOIN volunteer_email ve ON v.Volunteer_id = ve.Volunteer_id
                WHERE ve.Email = %s
            """, (email,))
            
            existing_volunteer = cursor.fetchone()
            
            if existing_volunteer:
                flash('A volunteer with this email already exists!', 'error')
                return redirect(url_for('public_volunteers'))
            
            # Insert new volunteer - ONLY Name column
            cursor.execute("INSERT INTO volunteer (Name) VALUES (%s)", (name,))
            volunteer_id = cursor.lastrowid
            
            # Insert email
            cursor.execute("INSERT INTO volunteer_email (Volunteer_id, Email) VALUES (%s, %s)", 
                         (volunteer_id, email))
            
            # Insert phone
            cursor.execute("INSERT INTO volunteer_phone (Volunteer_id, Phone) VALUES (%s, %s)", 
                         (volunteer_id, phone))
            
            # Insert skills
            for skill in skills:
                cursor.execute("INSERT INTO volunteer_skill (Volunteer_id, Skill) VALUES (%s, %s)", 
                             (volunteer_id, skill))
            
            connection.commit()
            flash('Thank you for registering as a volunteer! We will contact you soon.', 'success')
            return redirect(url_for('public_volunteers'))
            
        except Exception as e:
            connection.rollback()
            flash(f'Error processing registration: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    # For GET request, show the form
    return render_template('public/volunteers.html')

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 1
            session['username'] = username
            session['is_admin'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('admin/dashboard.html', 
                             total_donors=0, total_donations=0, 
                             total_events=0, total_beneficiaries=0,
                             recent_donations=[], upcoming_events=[])
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT COUNT(*) as total FROM donor")
        total_donors = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM donation")
        total_donations = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM event")
        total_events = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM beneficiary")
        total_beneficiaries = cursor.fetchone()['total']
        
        cursor.execute("""
    SELECT d.*, donor.Name as donor_name, ngo.Ngo_name 
    FROM donation d 
    JOIN donor ON d.Donor_id = donor.Donor_id 
    JOIN ngo ON d.Ngo_id = ngo.Ngo_id 
    ORDER BY d.Donation_id DESC LIMIT 5
""")
        recent_donations = cursor.fetchall()
        
        cursor.execute("""
            SELECT e.*, ngo.Ngo_name 
            FROM event e 
            JOIN ngo ON e.Ngo_id = ngo.Ngo_id 
            WHERE e.Event_date >= CURDATE() 
            ORDER BY e.Event_date ASC LIMIT 5
        """)
        upcoming_events = cursor.fetchall()
        
    except Exception as e:
        flash(f'Database error: {str(e)}', 'error')
        total_donors = total_donations = total_events = total_beneficiaries = 0
        recent_donations = upcoming_events = []
    
    cursor.close()
    connection.close()
    
    return render_template('admin/dashboard.html', 
                         total_donors=total_donors,
                         total_donations=total_donations,
                         total_events=total_events,
                         total_beneficiaries=total_beneficiaries,
                         recent_donations=recent_donations,
                         upcoming_events=upcoming_events)

@app.route('/admin/volunteers')
def admin_volunteers():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('admin/volunteers.html', volunteers=[])
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                v.Volunteer_id,
                v.Name,
                GROUP_CONCAT(DISTINCT vs.Skill) as skills,
                GROUP_CONCAT(DISTINCT ve.Email) as emails,
                GROUP_CONCAT(DISTINCT vp.Phone) as phones,
                COUNT(DISTINCT ev.Event_id) as events_count,
                SUM(ev.Hours_contributed) as total_hours
            FROM volunteer v
            LEFT JOIN volunteer_skill vs ON v.Volunteer_id = vs.Volunteer_id
            LEFT JOIN volunteer_email ve ON v.Volunteer_id = ve.Volunteer_id
            LEFT JOIN volunteer_phone vp ON v.Volunteer_id = vp.Volunteer_id
            LEFT JOIN event_volunteer ev ON v.Volunteer_id = ev.Volunteer_id
            GROUP BY v.Volunteer_id, v.Name
            ORDER BY total_hours DESC
        """)
        volunteers = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading volunteers: {str(e)}', 'error')
        volunteers = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('admin/volunteers.html', volunteers=volunteers)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/redistribute-funds')
def redistribute_funds():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        # First cursor for calling procedure
        cursor1 = connection.cursor()
        cursor1.callproc('RedistributeExcessDonations')
        connection.commit()
        cursor1.close()
        
        # Second cursor for fetching results (with dictionary=True)
        cursor2 = connection.cursor(dictionary=True)
        cursor2.execute("""
            SELECT
                s.Ngo_name as from_ngo,
                t.Ngo_name as to_ngo,
                fr.Amount,
                fr.Redistribution_date
            FROM fund_redistribution fr
            JOIN ngo s ON fr.Source_Ngo_id = s.Ngo_id
            JOIN ngo t ON fr.Target_Ngo_id = t.Ngo_id
            ORDER BY fr.Redistribution_date DESC
        """)
        redistributions = cursor2.fetchall()
        cursor2.close()
        
        flash('Funds redistributed successfully!', 'success')
        
    except Exception as e:
        connection.rollback()
        flash(f'Error redistributing funds: {str(e)}', 'error')
        redistributions = []
    finally:
        connection.close()
    
    return render_template('admin/redistribution_results.html', redistributions=redistributions)

@app.route('/admin/budget-audit')
def budget_audit():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('admin/budget_audit.html', audits=[])
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT * FROM budget_audit 
            ORDER BY Change_Timestamp DESC
        """)
        audits = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading budget audit: {str(e)}', 'error')
        audits = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('admin/budget_audit.html', audits=audits)

@app.route('/admin/donation-impact')
def donation_impact():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return render_template('admin/donation_impact.html', impacts=[])
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT
                don.Name AS Donor_Name,
                d.Amount AS Donation_Amount,
                d.Donation_date,
                n.Ngo_name AS NGO_Name,
                (SELECT COUNT(*) FROM beneficiary WHERE Ngo_id = n.Ngo_id) AS Beneficiaries_Supported
            FROM donation d
            JOIN donor don ON d.Donor_id = don.Donor_id
            JOIN ngo n ON d.Ngo_id = n.Ngo_id
            ORDER BY d.Donation_id DESC, d.Donation_date DESC
        """)
        impacts = cursor.fetchall()
        
    except Exception as e:
        flash(f'Error loading impact data: {str(e)}', 'error')
        impacts = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('admin/donation_impact.html', impacts=impacts)

if __name__ == '__main__':
    print("🚀 Starting NGO Management System...")
    if test_db_connection():
        print("🌐 Website running on http://localhost:5000")
        print("🔐 Admin panel: http://localhost:5000/admin/login")
        print("👥 Volunteer registration: http://localhost:5000/volunteers")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("💥 Failed to start. Check your database connection.")