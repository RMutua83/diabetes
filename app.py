from flask import Flask, render_template, request, redirect, url_for, session, flash
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from imblearn.combine import SMOTEENN
from joblib import dump, load
from sklearn.svm import SVC
import mysql.connector
import pandas as pd
import numpy as np
import bcrypt
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Paths for saving model and scaler
classifier_path = 'diabetes_model.pkl'
scaler_path = 'scaler.pkl'

# Train and save model if not already trained
def train_and_save_model():
    if not os.path.exists(classifier_path) or not os.path.exists(scaler_path):
        df = pd.read_csv('diabetes.csv')
        X, y = df.drop('Outcome', axis=1), df['Outcome']
        X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=20)
        scaler, svm = MinMaxScaler(), SVC()
        X_train_snn, y_train_snn = SMOTEENN(random_state=20).fit_resample(scaler.fit_transform(X_train), y_train)
        svm.fit(X_train_snn, y_train_snn)
        dump(svm, classifier_path)
        dump(scaler, scaler_path)
    return load(classifier_path), load(scaler_path)

classifier, scaler = train_and_save_model()

# Establish a database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="", 
        database="diabetespred")

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id, name, password = request.form['id'], request.form['name'], request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO health_promoters (promoterId, promoterName, promoterPassword) VALUES (%s, %s, %s)", (user_id, name, hashed_password))
            conn.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id, password = request.form['id'], request.form['password']
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT promoterId, promoterPassword FROM health_promoters WHERE promoterId = %s", (user_id,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
                session['user_id'] = user[0]
                flash('Login successful!', 'success')
                return redirect(url_for('prediction'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

# User logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Health administrator registration
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name, email, password = request.form['name'], request.form['email'], request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO health_administrators (healthName, healthEmail, healthPassword) VALUES (%s,%s, %s)", (name, email, hashed_password))
            conn.commit()
        flash('Admin registration successful! Please log in.', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin_register.html')

# Health administrator login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name, password = request.form['name'], request.form['password']
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT healthName, healthPassword FROM health_administrators WHERE healthName = %s", (name,))
            admin = cursor.fetchone()
            if admin and bcrypt.checkpw(password.encode('utf-8'), admin[1].encode('utf-8')):
                session['admin_id'] = admin[0]
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials. Please try again.', 'danger')
    return render_template('admin_login.html')

# Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please log in first as admin.', 'danger')
        return redirect(url_for('admin_login'))
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT promoterId, promoterName FROM health_promoters")
        users = cursor.fetchall()
    return render_template('admin_dashboard.html', users=users)

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Prediction page
@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            data = np.array([[float(request.form[field]) for field in 
                              ['pregnancies', 'glucose', 'BP', 'ST', 'insulin', 'BMI', 'DPF', 'age']]])
            result = "Positive" if classifier.predict(scaler.transform(data))[0] == 1 else "Negative"
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO predictions 
                                (promoterId, pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree, age, result) 
                                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                               (session['user_id'], *data[0], result))
                conn.commit()
            flash('Prediction result stored successfully!', 'success')
            return render_template('result.html', result=result)
        except ValueError:
            flash('Invalid input. Please enter valid numerical values.', 'danger')
    return render_template('prediction.html')

# Prediction report page
@app.route('/report')
def report():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM predictions")
        predictions = cursor.fetchall()
    return render_template('report.html', predictions=predictions)

if __name__ == '__main__':
    app.run(debug=True)
