from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_bcrypt import Bcrypt
import mysql.connector
from urllib.parse import quote as url_quote
import os



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Make sure to use a secure key in production

bcrypt = Bcrypt(app)
socketio = SocketIO(app)

def get_db_connection():
    conn = mysql.connector.connect(
        host="hopper.proxy.rlwy.net",
        user="root",
        password="zxyxhaUVPDNCsUSCEhEtVrPPTdlRnMIe",
        database="Event",
        port=45920
    )
    return conn

def execute_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()

def fetch_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

@app.route('/')
def index():
    events = fetch_query("SELECT * FROM event")
    return render_template('index.html', events=events)

@app.route('/post_event', methods=['GET', 'POST'])
def post_event():
    if request.method == 'POST':
        event_name = request.form.get('name')
        address = request.form.get('address')
        date = request.form.get('date')
        time = request.form.get('time')
        phone = request.form.get('phone')
        domain = request.form.get('domain')
        max_participants = request.form.get('max_participants')

        # Insert event details into the event table
        query = """
            INSERT INTO event (name, address, date, time, phone, domain, max_participants)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (event_name, address, date, time, phone, domain, max_participants)
        execute_query(query, params)
        return redirect(url_for('index'))

    return render_template('post_event.html')

@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
def register(event_id):
    event = fetch_query("SELECT * FROM event WHERE id = %s", (event_id,))
    if not event:
        return "Event not found", 404
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        team_members = request.form.get('team_members', '')
        college_name = request.form['college_name']
        branch = request.form['branch']
        year = request.form['year']
        if 'user_id' in session:
            user_id = session['user_id']
        else:
            return "User not logged in", 403
        
        query = """
            INSERT INTO registration (event_id, user_id, name, phone, team_members, college_name, branch, year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (event_id, user_id, name, phone, team_members, college_name, branch, year)
        try:
            execute_query(query, params)
        except Exception as e:
            return str(e), 500
        return redirect(url_for('event_detail', event_id=event_id))

    return render_template('register.html', event=event[0])

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = fetch_query("SELECT * FROM event WHERE id = %s", (event_id,))
    registrations = fetch_query("SELECT * FROM registration WHERE event_id = %s", (event_id,))
    return render_template('event_detail.html', event=event[0], registrations=registrations)

@app.route('/event/<int:event_id>/chat', methods=['GET', 'POST'])
def event_chat(event_id):
    event = fetch_query("SELECT * FROM event WHERE id = %s", (event_id,))
    if 'user_id' in session:
        user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))
        username = user[0]['name']
    else:
        username = 'Guest'
    
    return render_template('chat.html', event=event[0], username=username)

# @socketio.on('join')
# def handle_join(data):
#     username = data['username']
#     event_id = data['event_id']
#     room = f"event_{event_id}"
#     join_room(room)
#     emit('message', {'msg': f'{username} has joined the chat.'}, to=room)

# @socketio.on('message')
# def handle_message(data):
#     event_id = data['event_id']
#     room = f"event_{event_id}"
#     query = """
#         INSERT INTO messages (message, user_id, event_id) 
#         VALUES (%s, %s, %s)
#     """
#     params = (data['msg'], data['user_id'], event_id)
#     execute_query(query, params)
#     emit('message', {'username': data['username'], 'msg': data['msg']}, to=room)

# @socketio.on('leave')
# def handle_leave(data):
#     username = data['username']
#     event_id = data['event_id']
#     room = f"event_{event_id}"
#     leave_room(room)
#     emit('message', {'msg': f'{username} has left the chat.'}, to=room)

# @app.route('/event/<int:event_id>/messages')
# def get_messages(event_id):
#     messages = fetch_query("SELECT * FROM messages WHERE event_id = %s", (event_id,))
#     return {'messages': [{'username': fetch_query("SELECT name FROM user WHERE id = %s", (m['user_id'],))[0]['name'], 'message': m['message']} for m in messages]}

# @app.route('/event/<int:event_id>/participants')
# def get_participants(event_id):
#     registrations = fetch_query("SELECT * FROM registration WHERE event_id = %s", (event_id,))
#     return {'participants': [{'name': fetch_query("SELECT name FROM user WHERE id = %s", (r['user_id'],))[0]['name']} for r in registrations]}


from flask import Flask, render_template, request
from recommendations import get_recommendations  # Import the function

@app.route("/recommendations/<int:event_id>")
def show_recommendations(event_id):
    recommended_events = get_recommendations(event_id)
    return render_template("recommendations.html", events=recommended_events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = fetch_query("SELECT * FROM user WHERE email = %s", (email,))
        if user and bcrypt.check_password_hash(user[0]['password'], password):
            session['user_id'] = user[0]['id']
            return redirect(url_for('index'))
        else:
            return 'Invalid email or password', 401
    return render_template('login.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        query = """
            INSERT INTO user (name, email, password) 
            VALUES (%s, %s, %s)
        """
        params = (name, email, hashed_password)
        try:
            execute_query(query, params)
        except Exception as e:
            return str(e), 500
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))[0]
    upcoming_events = fetch_query("""
        SELECT * FROM event 
        WHERE date >= CURDATE() 
        AND id IN (SELECT event_id FROM registration WHERE user_id = %s)
    """, (user['id'],))
    
    past_events = fetch_query("""
        SELECT * FROM event 
        WHERE date < CURDATE() 
        AND id IN (SELECT event_id FROM registration WHERE user_id = %s)
    """, (user['id'],))

    badge = None
    registration_count = len(fetch_query("SELECT * FROM registration WHERE user_id = %s", (user['id'],)))
    if registration_count > 10:
        badge = 'gold'
    elif registration_count > 5:
        badge = 'red'

    return render_template('profile.html', user=user, upcoming_events=upcoming_events, past_events=past_events, badge=badge)

@app.route('/leaderboard')
def leaderboard():
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            u.name AS name, 
            COUNT(r.id) AS event_count
        FROM 
            user u
        JOIN 
            registration r ON u.id = r.user_id
        GROUP BY 
            u.name
        ORDER BY 
            event_count DESC
        LIMIT 10;
    """
    cursor.execute(query)
    leaderboard_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route('/report_event/<int:event_id>')
def report_event(event_id):
    return render_template('report_form.html', event_id=event_id)



@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    return redirect(url_for('profile'))

@app.route('/sponsor/<int:event_id>')
def sponsor_page(event_id):
    return render_template('sponsor.html', event_id=event_id)

@app.route('/apply_sponsorship/<int:event_id>', methods=['POST'])
def apply_sponsorship(event_id):
    business_name = request.form['business_name']
    contact_person = request.form['contact_person']
    email = request.form['email']
    phone = request.form['phone']
    message = request.form['message']

    event_organizer_email = "organizer@example.com"  
    subject = f"New Sponsorship Application from {business_name}"
    body = f"""
    Business Name: {business_name}
    Contact Person: {contact_person}
    Email: {email}
    Phone: {phone}
    Message: {message}
    """

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login("your_email@example.com", "your_password")  
            server.sendmail(email, event_organizer_email, f"Subject: {subject}\n\n{body}")
    except Exception as e:
        print(f"Error sending email: {e}")

    return redirect(url_for('event_detail', event_id=event_id))  




@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Use Railway's port
    socketio.run(app, host="0.0.0.0", port=port)
