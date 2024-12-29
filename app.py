from flask import Flask, render_template, request
import joblib
from keras.models import load_model
import pandas as pd
import numpy as np

app = Flask(__name__)

# Load the model and scaler
try:
    model = load_model('myModel.keras')
    scaler = joblib.load('scaler.pkl')
    print("Model and scaler loaded successfully.")
except Exception as e:
    print(f"Error loading model or scaler: {e}")
    model = None
    scaler = None

# Assume these are your column names used during training
MODEL_COLUMNS = ['Rice', 'Wheat', 'Atta (Wheat)', 'Gram Dal', 'Tur/Arhar Dal']
LOOK_BACK = 7  # Ensure this matches your training look_back

# Load your historical data (replace with your actual loading method)
try:
    data = pd.read_csv("data/data_mean.csv")
    data['Date'] = pd.to_datetime(data['Date'])
    print("Historical data loaded successfully.")
except Exception as e:
    print(f"Error loading historical data: {e}")
    data = None

def prepare_dataset_for_prediction(dataset, look_back):
    X = []
    for i in range(len(dataset) - look_back):
        a = dataset[i:(i + look_back), :]
        X.append(a)
    return np.array(X)

def predict_future_date(data, target_date_str, model, scaler, look_back, model_columns):
    if model is None or scaler is None or data is None:
        return "Model, scaler, or historical data not loaded."

    try:
        target_date = pd.to_datetime(target_date_str)
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."

    data['Date'] = pd.to_datetime(data['Date'])
    end_date = data['Date'].max()

    if target_date <= end_date:
        return data[data['Date'] == target_date][model_columns].map("{:.2f}".format)
    else:
        last_data = data.tail(look_back)[model_columns].values
        last_data_scaled = scaler.transform(last_data)
        last_data_scaled = last_data_scaled.reshape((1, look_back, len(model_columns)))

        current_date = end_date
        while current_date < target_date:
            prediction_scaled = model.predict(last_data_scaled, verbose=0)
            prediction = scaler.inverse_transform(prediction_scaled)[0]

            # Append the prediction to the historical data (for the next iteration)
            new_row_data = {col: prediction[i] for i, col in enumerate(model_columns)}
            new_row_data['Date'] = current_date + pd.DateOffset(days=1)
            data = pd.concat([data, pd.DataFrame([new_row_data])], ignore_index=True)

            # Update last_data_scaled for the next prediction
            new_input_scaled = np.append(last_data_scaled[:, 1:, :], prediction_scaled[:, np.newaxis, :], axis=1)
            last_data_scaled = new_input_scaled
            current_date += pd.DateOffset(days=1)

        return pd.DataFrame([prediction], columns=model_columns).map("{:.2f}".format)

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction_result = None
    if request.method == 'POST':
        future_date = request.form['future_date']
        if model and scaler and data is not None:
            prediction_result = predict_future_date(data.copy(), future_date, model, scaler, LOOK_BACK, MODEL_COLUMNS)
        else:
            prediction_result = "Model or scaler not loaded."
    return render_template('index.html', prediction_result=prediction_result)

if __name__ == '__main__':
    app.run(debug=True)