from flask import Flask, render_template, request, redirect, url_for, session, flash
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from imblearn.combine import SMOTEENN
from joblib import dump, load
from sklearn.svm import SVC
import mysql.connector
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the model and scaler
classifier_path = 'diabetes_model.pkl'
scaler_path = 'scaler.pkl'

if not os.path.exists(classifier_path) or not os.path.exists(scaler_path):
    def train_and_save_model():
        df = pd.read_csv('diabetes.csv')

        X = df.drop('Outcome', axis=1)
        y = df['Outcome']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=20)
        scaler = MinMaxScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        svm = SVC()

        snn = SMOTEENN(random_state=20)
        X_train_snn, y_train_snn = snn.fit_resample(X_train_scaled, y_train)

        svm.fit(X_train_snn, y_train_snn)
        dump(svm, classifier_path)
        dump(scaler, scaler_path)
        return svm, scaler

    classifier, scaler = train_and_save_model()
else:
    classifier = load(classifier_path)
    scaler = load(scaler_path)

# Establish database connection
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="diabetespred"
    )

    if db.is_connected():
        print("Successfully connected to the database")
    cursor = db.cursor()

except mysql.connector.Error as e:
    print(f"Error while connecting to MySQL: {e}")
    db = None

# Function to insert user registration data into the database
def registration(id, name, email, password):
    try:
        query = "INSERT INTO users (id, name, email, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (id, name, email, password))
        db.commit()
        flash('You have successfully registered! Please log in.', 'success')
    except mysql.connector.Error as e:
        flash(f"Error while inserting data into MySQL: {e}", 'danger')

# Function to verify user credentials during login
def verify(id, password):
    try:
        query = "SELECT * FROM users WHERE id = %s AND password = %s"
        cursor.execute(query, (id, password))
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

        registration(user_id, name, email, password)
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['id']
        password = request.form['password']

        user = verify(user_id, password)

        if user:
            session['user_id'] = user[0]  # Store user ID in session
            flash('Login successful!', 'success')
            return redirect(url_for('prediction'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            patient_id = session['user_id']  # Use logged-in user's ID as patient ID
            val1 = float(request.form['pregnancies'])
            val2 = float(request.form['glucose'])
            val3 = float(request.form['BP'])
            val4 = float(request.form['ST'])
            val5 = float(request.form['insulin'])
            val6 = float(request.form['BMI'])
            val7 = float(request.form['DPF'])
            val8 = float(request.form['age'])

            data = np.array([[val1, val2, val3, val4, val5, val6, val7, val8]])
            data_scaled = scaler.transform(data)
            my_prediction = classifier.predict(data_scaled)

            result = "Positive" if my_prediction[0] == 1 else "Negative"

            # Store prediction result in database
            try:
                query = "INSERT INTO predictions (patient_id, pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree, age, result) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (patient_id, val1, val2, val3, val4, val5, val6, val7, val8, result))
                db.commit()
                flash('Prediction result stored successfully!', 'success')
            except mysql.connector.Error as e:
                flash(f"Error while inserting prediction into MySQL: {e}", 'danger')

            return render_template('result.html', result=result)
        except ValueError:
            flash('Invalid input. Please enter valid numerical values.', 'danger')

    return render_template('prediction.html')

@app.route('/logout')
def logout():
    session.pop('id', None)
    return redirect(url_for('home'))

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/report')
def report():
    try:
        cursor.execute("SELECT * FROM predictions")
        predictions = cursor.fetchall()
        return render_template('report.html', predictions=predictions)
    except mysql.connector.Error as e:
        flash(f"Error while fetching predictions from MySQL: {e}", 'danger')
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
