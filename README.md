# AgriCast

Commodity price forecasting web app built with Flask, Keras/TensorFlow, and scikit-learn.

## Overview
- Backend: `Flask` app (`app.py`) serving a single route `/` for rendering predictions.
- Model: Keras model file `myModel.keras` that predicts next-day prices for a fixed set of commodities using a sliding window of the last 7 days.
- Scaling: scikit-learn scaler `scaler.pkl` used to scale inputs (and inverse-transform predictions).
- Data: Historical daily series in `data/data_mean.csv` (primary), with alternate `data/data_median.csv`, plus the original datasets `data.csv` (wider feature set) and `raw_data.csv` (compact schema).
- Frontend: Jinja2 template `templates/index.html` with `static/script.js` and `static/style.css` for UI, date picker, crop selection, and a Chart.js placeholder.

## Project structure
```
app.py
README.md
requirements.txt
myModel.keras
scaler.pkl
static/
  script.js
  style.css
templates/
  index.html
data/
  data_mean.csv
  data_median.csv
raw_data.csv
data.csv
```

## Data schemas
- `data/data_mean.csv` and `data/data_median.csv` (used by app):
  - Columns: `Day, Month, Year, Rice, Wheat, Atta (Wheat), Gram Dal, Tur/Arhar Dal, Date`
  - `Date` is a full timestamp string (e.g., `2016-01-01 00:00:00.000000000`), parsed into pandas `datetime64`.
  - App uses only: `Date` + feature columns defined in `MODEL_COLUMNS`.
- `raw_data.csv`: compact format with `Day, Month, Year` plus the five commodities used by the model.
- `data.csv`: wide format with 20+ commodities and staples; not directly used by the current app.

## Backend flow (app.py)
- Imports: Flask, joblib, Keras load_model, pandas, numpy, json.
- Loads:
  - `model = load_model('myModel.keras')`
  - `scaler = joblib.load('scaler.pkl')`
  - Historical data `data = pd.read_csv('data/data_mean.csv')` + parse `Date`.
- Constants:
  - `MODEL_COLUMNS = ['Rice', 'Wheat', 'Atta (Wheat)', 'Gram Dal', 'Tur/Arhar Dal']`
  - `LOOK_BACK = 7`
- Core function: `predict_future_date(data, target_date_str, model, scaler, look_back, model_columns)`
  - If `target_date <= end_date` (last date in historical data):
    - Returns the row for that date, restricted to `MODEL_COLUMNS`, formatted to 2 decimals.
  - Else (future date):
    - Takes the last `look_back` days of the selected columns, scales them, reshapes to `(1, look_back, n_features)`.
    - Iteratively predicts next day in scaled space, inverse transforms to price units, and appends to a working copy of the data; slides the window until reaching the target date.
    - Returns a single-row DataFrame formatted to 4 decimals.
  - Notes:
    - Caller passes `data.copy()` so requests don’t mutate the global DataFrame.
    - If model/scaler/data fail to load, returns an error message string.
- Route `/` (GET/POST):
  - Renders `index.html` with:
    - `default_date` = max historical date (as `YYYY-MM-DD`).
    - `available_crops` = `MODEL_COLUMNS`.
  - On POST, reads `future_date` and a JSON list of selected crops (`crops`), runs prediction, and sends a subset DataFrame (or error string) back to the template.

## Frontend flow
- `templates/index.html`:
  - Left panel: Flatpickr inline date picker bound to hidden input `future_date`.
  - Crop selection: Toggle buttons for each commodity with “Select All” control; selected list is serialized to hidden input `crops` as JSON string.
  - Result area: Renders a table if `prediction_result` is a DataFrame; otherwise shows error text.
  - Chart.js canvas present; actual `chartData` is not yet provided from the backend, so the chart is currently a placeholder.
- `static/script.js`:
  - Manages crop button selection, select-all toggle, hidden inputs, and loader visibility on form submit.
  - Initializes Flatpickr with `defaultDate = {{ default_date }}`.
  - Chart.js code expects a global `chartData` object; not provided yet, so no chart shows by default.
- `static/style.css`:
  - Theme/typography, responsive grid, styled buttons, date picker theming, table styles, and chart container.

## Running the app
1. Create a Python environment (Python 3.10+ recommended for TensorFlow 2.19):
   - Windows (PowerShell):
     - Optional: `py -3.10 -m venv .venv; .venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start the server:
   - `python app.py`
4. Open http://127.0.0.1:5000/ in your browser.

## Troubleshooting
- Model/scaler load failures:
  - Ensure `myModel.keras` and `scaler.pkl` exist at project root and were created with compatible library versions.
  - If `scaler.pkl` was saved with a different scikit-learn version, you may hit deserialization errors. Pin to the original version if possible.
- TensorFlow/Keras compatibility:
  - Requirements pin `tensorflow==2.19.0` and `keras==3.9.2`. If the model was trained with older TF/Keras, consider aligning versions used during training and serving.
- Date selection:
  - Past dates must exist in `data/data_mean.csv` to return historical rows. Missing dates will result in empty selections; the code doesn’t explicitly handle “gap” days.
- Performance:
  - Far-future dates will run a day-by-day iterative loop (could be slow for very distant dates). Consider adding a max horizon.
- Production safety:
  - `app.run(debug=True)` is for development only.

## Extending the app
- Provide charts: Generate `chartData` server-side (last N days + predicted point) and render as a JSON script block in the template.
- Validation: Enforce allowed date ranges in Flatpickr (min/max), and validate server-side.
- API endpoint: Add `/api/forecast?date=YYYY-MM-DD&crops=[...]` that returns JSON for SPA usage.
- Caching: Cache predictions per date to avoid repeated computation when iterating many days ahead.
- Columns flexibility: If you change `MODEL_COLUMNS` in training, update both the scaler and app.

## Key contracts
- Inputs: `future_date` as `YYYY-MM-DD`; `crops` as JSON array of strings matching `MODEL_COLUMNS`.
- Output: For valid requests, a single-row DataFrame of selected crops with formatted prices; otherwise a string error.
- Error modes: Missing/invalid date, model/scaler/data not loaded, version incompatibilities.

