from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Get data from the form
    int_features = [float(x) for x in request.form.values()]
    # Just for demonstration, we will return the sum of the input values as the prediction
    prediction = sum(int_features)

    return render_template('index.html', prediction_text='Sum of input values: {}'.format(prediction))

if __name__ == "__main__":
    app.run(debug=True)
