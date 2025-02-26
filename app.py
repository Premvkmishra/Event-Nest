from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_bcrypt import Bcrypt
import mysql.connector
import smtplib
import re  # Import the regular expression module
from flask_debugtoolbar import DebugToolbarExtension
import os  # for file handling
from werkzeug.utils import secure_filename  # for file uploads
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'  # Make sure to use a secure key in production
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False  # Don't intercept redirects with the toolbar
toolbar = DebugToolbarExtension(app)

bcrypt = Bcrypt(app)
socketio = SocketIO(app)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  
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


def add_message_to_chatroom_chat(event_id, email, message):
    conn = None  
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO chatroom_chat (event_id, email, message)
            VALUES (%s, %s, %s);
        """
        val = (event_id, email, message)

        print(f"SQL Query: {sql}")  
        print(f"SQL Values: {val}") 

        cursor.execute(sql, val)
        conn.commit()

        print(f"Cursor rowcount: {cursor.rowcount}")  # print rowcount

        if cursor.rowcount > 0:
            print(cursor.rowcount, "record inserted.")
        else:
            print("Message not inserted.")
        cursor.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if conn:  
            conn.close()
            print("MySQL connection is closed")


def simulate_update():
    
    updated_values = {
        'setting1': 'new value 1',
        'setting2': 'new value 2',
        # Add more settings as needed
    }
    return updated_values

# Corrected filter registration (NO FUNCTION REDEFINITION HERE!)
# @app.template_filter('highlight_search_term')
# def highlight_search_term(text, search_query):
#     if search_query and text:
#         try:
#             pattern = re.compile(re.escape(search_query), re.IGNORECASE)
#             return pattern.sub(r'<span class="highlight">\g<0></span>', text)
#         except re.error as e:  # Catch potential regex errors.
#             print(f"Regex error: {e}")
#             return text  # Return the original text if regex fails
#     return text



@app.route('/')
def index():
    search_query = request.args.get('search')
    events = []
    try:
        if search_query:
            query = """
                SELECT * FROM event
                WHERE name LIKE %s OR address LIKE %s OR domain LIKE %s
            """
            params = (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
            events = fetch_query(query, params)
        else:
            events = fetch_query("SELECT * FROM event")
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        # Handle the error appropriately, e.g., render an error template
        return render_template('error.html', message="Database error occurred.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Handle unexpected errors
        return render_template('error.html', message="An unexpected error occurred.")

    return render_template('index.html', events=events, username="")


# @app.route('/')
# def index():
#     search_query = request.args.get('search', '')  # Get the search query, defaulting to '' if it's missing
#     events = []
#     error_message = None
#     try:
#         if search_query:
#             query = """
#                 SELECT * FROM event
#                 WHERE name LIKE %s OR address LIKE %s OR domain LIKE %s
#             """
#             params = (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
#             events = fetch_query(query, params)

#             if not events:
#                 error_message = "No events found matching your search criteria." ye galat h ok
#                 # You could also redirect to another page or render a different template
#                 # return render_template('no_results.html', search_query=search_query)
#         else:
#             events = fetch_query("SELECT * FROM event")
#     except mysql.connector.Error as e:
#         print(f"Database error: {e}")
#         error_message = "A database error occurred. Please try again later."
#         # Handle the error appropriately, e.g., render an error template
#         # return render_template('error.html', message="Database error occurred.")
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         error_message = "An unexpected error occurred. Please try again later."
#         # Handle unexpected errors
#         # return render_template('error.html', message="An unexpected error occurred.")

#     return render_template('index.html', events=events, username="", search_query=search_query, error_message=error_message)


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
    if not event:
        return "Event not found", 404

    if 'user_id' in session:
        user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))
        if user:
            user_email = user[0]['email']
            username = user[0]['name']
        else:
            user_email = None
            username = 'Unknown User'
    else:
        user_email = None  # Or handle guest users differently
        username = 'Guest'  # Default username

    if request.method == 'POST':
        message = request.form.get('message')
        if user_email and message:  # Only add a message if the user is logged in and the message isn't empty.
            print(f"Email being passed: {user_email}")
            print(f"Message being passed: {message}")
            add_message_to_chatroom_chat(event_id, user_email, message)  # Save to the chatroom_chat table
            socketio.emit('new_message', {'event_id': event_id, 'username': username, 'message': message}, room=f'event_{event_id}') # Broadcast message to chatroom
        return redirect(url_for('event_chat', event_id=event_id))  # Redirect to refresh the chat

    # Fetch chat messages to display (latest first)
    chat_messages = fetch_query("SELECT * FROM chatroom_chat WHERE event_id = %s ORDER BY timestamp DESC", (event_id,))

    return render_template('chat.html', event=event[0], username=username, chat_messages=chat_messages)


@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join')
def handle_join(data):
    username = data['username']
    event_id = data['event_id']
    room = f"event_{event_id}"
    join_room(room)
    print(f'{username} joined room {room}')
    emit('message', {'msg': f'{username} has joined the chat.'}, room=room)

@socketio.on('leave')
def handle_leave(data):
    username = data['username']
    event_id = data['event_id']
    room = f"event_{event_id}"
    leave_room(room)
    emit('message', {'msg': f'{username} has left the chat.'}, room=room)

@socketio.on('send_message')
def handle_message(data):
    event_id = data['event_id']
    username = data['username']
    message = data['message']
    room = f"event_{event_id}"
    emit('message', {'username': username, 'msg': message}, room=room)


# @socketio.on('message')
# def handle_message(data):
#     event_id = data['event_id]
#     room = f"event_{event_id}"
#     query = """
#         INSERT INTO messages (message, user_id, event_id)
#         VALUES (%s, %s, %s)
#     """
#     params = (data['msg], data['user_id], event_id)
#     execute_query(query, params)
#     emit('message', {'username': data['username'], 'msg': data['msg']}, to=room)

# @socketio.on('leave')
# def handle_leave(data):
#     username = data['username]
#     event_id = data['event_id]
#     room = f"event_{event_id}"
#     leave_room(room)
#     emit('message', {'msg': f'{username} has left the chat.'}, to=room)

# @app.route('/event/<int:event_id>/messages')
# def get_messages(event_id):
#     messages = fetch_query("SELECT * FROM messages WHERE event_id = %s", (event_id,))
#     return {'messages': [{'username': fetch_query("SELECT name FROM user WHERE id = %s", (m['user_id],))[0]['name'], 'message': m['message']} for m in messages]}

# @app.route('/event/<int:event_id>/participants')
# def get_participants(event_id):
#     registrations = fetch_query("SELECT * FROM registration WHERE event_id = %s", (event_id,))
#     return {'participants': [{'name': fetch_query("SELECT name FROM user WHERE id = %s", (r['user_id],))[0]['name'], 'message': m['message']} for m in messages]}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = fetch_query("SELECT * FROM user WHERE email = %s", (email,))
        if user and bcrypt.check_password_hash(user[0]['password'], password):
            session['user_id'] = user[0]['id']
            return redirect(url_for('profile'))
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


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = fetch_query("SELECT * FROM user WHERE id = %s", (user_id,))[0]

    try:
        # Fetch events the user is registered for and are in the future
        upcoming_events = fetch_query("""
            SELECT e.*
            FROM event e
            JOIN registration r ON e.id = r.event_id
            WHERE r.user_id = %s AND e.date >= %s
            ORDER BY e.date
        """, (user_id, date.today()))

        # Fetch events the user is registered for and are in the past
        past_events = fetch_query("""
            SELECT e.*
            FROM event e
            JOIN registration r ON e.id = r.event_id
            WHERE r.user_id = %s AND e.date < %s
            ORDER BY e.date DESC
        """, (user_id, date.today()))

    except Exception as e:
        flash(f"Error fetching events: {e}", "error")  # Show error to user
        upcoming_events = []
        past_events = []

    badge = None
    registration_count = len(fetch_query("SELECT * FROM registration WHERE user_id = %s", (user['id'],)))
    if registration_count > 10:
        badge = 'gold'
    elif registration_count > 5:
        badge = 'red'

    profile_pic = user.get('profile_pic', 'See.jpeg')

    return render_template('profile.html', user=user, upcoming_events=upcoming_events, past_events=past_events, badge=badge, profile_pic=profile_pic)


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

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))[0]  # Fetch user data

    if request.method == 'POST':
        # Simulate updating settings data
        updated_settings = simulate_update()  # Replace with your data update logic
        flash('Settings saved successfully!', 'success')  # Flash a success message

        # Optionally, persist the updated settings to the database or session
        # Example: session['user_settings'] = updated_settings
        # Or update the settings directly in the database

        return redirect(url_for('profile'))  # Redirect back to profile after saving

    # Render the settings form
    return render_template('settings.html', user=user)

@app.route('/appearance', methods=['GET', 'POST'])
def appearance():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))[0]  # Fetch user data

    if request.method == 'POST':
        # Simulate updating appearance settings data
        updated_appearance = simulate_update()  # Replace with your data update logic
        flash('Appearance settings updated!', 'success')  # Flash a success message

        # Optionally, persist the updated appearance settings to the database or session
        # Example: session['user_appearance'] = updated_appearance
        # Or update the settings directly in the database

        return redirect(url_for('profile'))  # Redirect back to profile after saving

    # Render the appearance form
    return render_template('appearance.html', user=user)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))[0]  # Fetch user data

    if request.method == 'POST':
        # Simulate updating dashboard data
        updated_dashboard = simulate_update()  # Replace with your data update logic
        flash('Dashboard updated!', 'success')  # Flash a success message

        # Optionally, persist the updated dashboard data to the database or session
        # Example: session['user_dashboard'] = updated_dashboard
        # Or update the settings directly in the database

        return redirect(url_for('profile'))  # Redirect back to profile after saving

    # Render the dashboard
    return render_template('dashboard.html', user=user)


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))[0]  # Fetch user data

    if request.method == 'POST':
        feedback_text = request.form['feedback']
        # In a real application, store the feedback in a database
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback'))  # Redirect to clear the form
    return render_template('feedback.html', user=user)



@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = fetch_query("SELECT * FROM user WHERE id = %s", (session['user_id'],))[0]

    # Update basic profile information
    name = request.form['name']
    email = request.form['email']

    # Handle profile picture upload
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename) #Sanitize filename for security
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            profile_pic = filepath  # Save path in the user data
            # Update user data in the database
            query = """
                UPDATE user
                SET name = %s, email = %s, profile_pic = %s
                WHERE id = %s
            """
            params = (name, email, profile_pic, user_id)
            try:
                execute_query(query, params)
            except Exception as e:
                return str(e), 500
        else:
            flash('Invalid file format. Please upload an image.', 'error')
            return redirect(url_for('profile'))
    else:
        # Update user data in the database without profile_pic
        query = """
            UPDATE user
            SET name = %s, email = %s
            WHERE id = %s
        """
        params = (name, email, user_id)
        try:
            execute_query(query, params)
        except Exception as e:
            return str(e), 500

    flash('Profile updated successfully!', 'success')
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


@app.route('/unregister/<int:event_id>', methods=['POST'])
def unregister(event_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        # Verify registration exists
        registration = fetch_query("""
            SELECT * FROM registration
            WHERE event_id = %s AND user_id = %s
        """, (event_id, user_id))

        if not registration:
            flash("You are not registered for this event.", "error")
            return redirect(url_for('event_detail', event_id=event_id))

        # Remove registration
        execute_query("""
            DELETE FROM registration
            WHERE event_id = %s AND user_id = %s
        """, (event_id, user_id))

        flash("Successfully unregistered from event.", "success")

    except Exception as e:
        flash(f"Error unregistering from event: {e}", "error")

    return redirect(url_for('event_detail', event_id=event_id))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    socketio.run(app, debug=True)