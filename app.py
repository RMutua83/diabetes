import mysql.connector

from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Establish database connection
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",           
        password="",           
        database="users"
    )

    if db.is_connected():
        print("Successfully connected to the database")
    cursor = db.cursor()

except mysql.connector.Error as e:
    print(f"Error while connecting to MySQL: {e}")
    db = None

# Function to insert user registration data into the database
def insert_user(user_id, name, email, password):
    try:
        query = "INSERT INTO tbl_users (id, name, email, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, name, email, password))
        db.commit()
        flash('You have successfully registered!', 'success')

    except mysql.connector.Error as e:
        flash(f"Error while inserting data into MySQL: {e}", 'danger')

# Function to verify user credentials during login
def verify_user_credentials(user_id, password):
    try:
        query = "SELECT * FROM tbl_users WHERE id = %s AND password = %s"
        cursor.execute(query, (user_id, password))
        user = cursor.fetchone()
        return user

    except mysql.connector.Error as e:
        print(f"Error while querying MySQL: {e}")
        return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        insert_user(user_id, name, email, password)
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['id']
        password = request.form['password']

        user = verify_user_credentials(user_id, password)

        if user:
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    return redirect(url_for('prediction'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)  
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
