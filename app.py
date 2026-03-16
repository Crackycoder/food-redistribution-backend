from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Iphone@7'
app.config['MYSQL_DB'] = 'food_redistribution'

mysql = MySQL(app)

# Register
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    phone = data['phone_number']
    email = data['email']
    password = hashlib.md5(data['password'].encode()).hexdigest()
    role = data['role']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (name, phone_number, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (name, phone, email, password, role))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'User registered successfully'})

# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = hashlib.md5(data['password'].encode()).hexdigest()
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()
    if user:
        return jsonify({'message': 'Login successful', 'user_id': user[0], 'name': user[1], 'role': user[5]})
    return jsonify({'message': 'Invalid credentials'}), 401

# Add Donation
@app.route('/add-donation', methods=['POST'])
def add_donation():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO food_donations (donor_id, food_type, quantity, location, pickup_time, description, gmaps_link) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (data['donor_id'], data['food_type'], data['quantity'], data['location'], data['pickup_time'], data['description'], data['gmaps_link']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Donation added successfully'})

# Get All Donations
@app.route('/donations', methods=['GET'])
def get_donations():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT fd.*, u.name, u.phone_number 
        FROM food_donations fd 
        JOIN users u ON fd.donor_id = u.user_id 
        WHERE fd.status='available'
    """)
    donations = cur.fetchall()
    cur.close()
    result = []
    for d in donations:
        result.append({
            'donation_id': d[0],
            'donor_id': d[1],
            'food_type': d[2],
            'quantity': d[3],
            'location': d[4],
            'pickup_time': str(d[5]),
            'description': d[6],
            'status': d[7],
            'gmaps_link': d[8],
            'donor_name': d[9],
            'donor_phone': d[10]
        })
    return jsonify(result)

# Claim Donation
@app.route('/claim-donation', methods=['POST'])
def claim_donation():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM claims WHERE donation_id=%s", (data['donation_id'],))
    existing = cur.fetchone()
    if existing:
        return jsonify({'message': 'Donation already claimed'}), 400
    cur.execute("INSERT INTO claims (donation_id, volunteer_id) VALUES (%s, %s)",
                (data['donation_id'], data['volunteer_id']))
    cur.execute("UPDATE food_donations SET status='claimed' WHERE donation_id=%s",
                (data['donation_id'],))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Donation claimed successfully'})

# Send Message
@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO messages (donation_id, sender_id, message) VALUES (%s, %s, %s)",
                (data['donation_id'], data['sender_id'], data['message']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Message sent'})

# Get Messages
@app.route('/messages/<int:donation_id>', methods=['GET'])
def get_messages(donation_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT m.*, u.name 
        FROM messages m 
        JOIN users u ON m.sender_id = u.user_id 
        WHERE m.donation_id=%s 
        ORDER BY m.sent_at ASC
    """, (donation_id,))
    messages = cur.fetchall()
    cur.close()
    result = []
    for m in messages:
        result.append({
            'message_id': m[0],
            'donation_id': m[1],
            'sender_id': m[2],
            'message': m[3],
            'sent_at': str(m[4]),
            'sender_name': m[5]
        })
    return jsonify(result)

# Get User Donations
@app.route('/user-donations/<int:user_id>', methods=['GET'])
def user_donations(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM food_donations WHERE donor_id=%s", (user_id,))
    donations = cur.fetchall()
    cur.close()
    result = []
    for d in donations:
        result.append({
            'donation_id': d[0],
            'food_type': d[2],
            'quantity': d[3],
            'location': d[4],
            'pickup_time': str(d[5]),
            'status': d[7]
        })
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)