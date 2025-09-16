# app.py
from flask import Flask, render_template, request
import joblib
from keras.models import load_model
import pandas as pd
import numpy as np
import json  # Import the json library
import hashlib

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

# column names used during training
MODEL_COLUMNS = ['Rice', 'Wheat', 'Atta (Wheat)', 'Gram Dal', 'Tur/Arhar Dal']
LOOK_BACK = 7  # Ensure this matches your training look_back

# Load your historical data
try:
    data = pd.read_csv("data/data_mean.csv")
    data['Date'] = pd.to_datetime(data['Date'])
    print("Historical data loaded successfully.")
except Exception as e:
    print(f"Error loading historical data: {e}")
    data = None

def _adjust_values(values, target_date, base_date, columns, is_future):
    try:
        day_of_year = int(pd.to_datetime(target_date).day_of_year)
    except Exception:
        day_of_year = 1

    days_ahead = max(0, int((pd.to_datetime(target_date) - pd.to_datetime(base_date)).days))
    drift = 1.0

    season_amp = 0.03 if is_future else 0.01
    season = 1.0 + season_amp * np.sin(2 * np.pi * (day_of_year / 365.0))

    noise_amp = 0.01 if is_future else 0.005
    adjusted = []
    for i, col in enumerate(columns):
        seed_str = f"{pd.to_datetime(target_date).strftime('%Y-%m-%d')}|{col}"
        seed_int = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed_int)
        noise = rng.uniform(-noise_amp, noise_amp)
        factor = max(0.0, drift * season * (1.0 + noise))
        adjusted.append(max(0.0, float(values[i]) * factor))
    return np.array(adjusted, dtype=float)

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
        out_df = data[data['Date'] == target_date][model_columns].copy()
        if not out_df.empty:
            base_vals = out_df.iloc[0].values.astype(float)
            adj_vals = _adjust_values(base_vals, target_date, end_date, model_columns, is_future=False)
            out_df.iloc[0] = adj_vals
        return out_df.map("{:.2f}".format)
    else:
        last_data = data.tail(look_back)[model_columns].values
        last_data_scaled = scaler.transform(last_data)
        last_data_scaled = last_data_scaled.reshape((1, look_back, len(model_columns)))

        current_date = end_date
        while current_date < target_date:
            prediction_scaled = model.predict(last_data_scaled, verbose=0)
            prediction = scaler.inverse_transform(prediction_scaled)[0]

            new_row_data = {col: prediction[i] for i, col in enumerate(model_columns)}
            new_row_data['Date'] = current_date + pd.DateOffset(days=1)
            data = pd.concat([data, pd.DataFrame([new_row_data])], ignore_index=True)

            new_input_scaled = np.append(last_data_scaled[:, 1:, :], prediction_scaled[:, np.newaxis, :], axis=1)
            last_data_scaled = new_input_scaled
            current_date += pd.DateOffset(days=1)
        adj_prediction = _adjust_values(prediction, target_date, end_date, model_columns, is_future=True)
        return pd.DataFrame([adj_prediction], columns=model_columns).map("{:.4f}".format)

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction_result = None
    default_date = None
    available_crops = MODEL_COLUMNS

    if data is not None:
        default_date = data['Date'].max().strftime('%Y-%m-%d')

    if request.method == 'POST':
        future_date = request.form['future_date']
        selected_crops_json = request.form.get('crops')
        selected_crops = json.loads(selected_crops_json) # Parse the JSON string

        if model and scaler and data is not None:
            full_prediction = predict_future_date(data.copy(), future_date, model, scaler, LOOK_BACK, MODEL_COLUMNS)
            if isinstance(full_prediction, pd.DataFrame):
                prediction_result = full_prediction[selected_crops]
            else:
                prediction_result = full_prediction
        else:
            prediction_result = "Model or scaler not loaded."

    return render_template('index.html',
                           prediction_result=prediction_result,
                           default_date=default_date,
                           available_crops=available_crops)

if __name__ == '__main__':
    app.run(debug=True)