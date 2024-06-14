import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

db = None

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",      # Replace with your MySQL username
        password="",  # Replace with your MySQL password
        database="users"
    )

    if db.is_connected():
        print("Successfully connected to the database")

except mysql.connector.Error as e:
    print(f"Error while connecting to MySQL: {e}")

# Ensure db is not None before using it
if db:
    cursor = db.cursor()
else:
    # Handle the case where db is None (e.g., connection failed)
    print("Database connection is not established.")


@app.route('/register' ,methods=['GET', 'POST'])
def register():
    global db

    if request.method == 'POST':
        user_id = request.form['id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        try:
            if db and db.is_connected():
                cursor = db.cursor()
                query = "INSERT INTO tbl_users (id, name, email, password) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (user_id, name, email, password))
                db.commit()
                cursor.close()

                flash('You have successfully registered!', 'success')
                return redirect(url_for('login'))
            else:
                flash('Database connection is not established.', 'danger')
                return redirect(url_for('register'))

        except mysql.connector.Error as e:
            flash(f"Error while inserting data into MySQL: {e}", 'danger')
            return redirect(url_for('register'))
        
        # Add a print statement for debugging
        print("Registration successful:", user_id, name, email)
    
    return render_template('register.html')
# Function to verify user credentials
def verify_user_credentials(user_id, password):
    try:
        cursor = db.cursor()
        query = "SELECT * FROM tbl_users WHERE id = %s AND password = %s"
        cursor.execute(query, (user_id, password))
        user = cursor.fetchone()  # Fetch one row

        cursor.close()
        return user  # Return user data if found, otherwise None

    except mysql.connector.Error as e:
        print(f"Error while querying MySQL: {e}")
        return None

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
            return redirect(url_for('login'))

    # If GET request, render the login form
    return render_template('login.html')

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/logout')
def logout():
    session.pop('id', None)
    return redirect(url_for('home'))
  
if __name__ == '__main__':
    app.run(debug=True)
