# Dynamic Machine Data Management & Local Risk Prediction

A full-stack machine management application built using Flask, MySQL, JavaScript and scikit-learn. It supports configurable machine attributes, dynamic forms, CRUD operations and local machine risk prediction.

## Features

- Create text, number and dropdown machine fields.
- Edit and delete custom fields.
- Automatically generate machine forms from field configurations.
- Add, view, edit and delete machine records.
- Store machine attributes using MySQL JSON columns.
- Add optional attributes such as Humidity without database schema changes.
- Predict Low, Medium or High Risk using a local Random Forest classifier.
- Responsive dashboard interface.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | scikit-learn, NumPy |
| Testing | pytest |

## Installation

Requires Python and a running MySQL server.

1. Clone this repository.
2. Open the project folder.
3. Create a virtual environment:

   `python -m venv .venv`

4. Activate it on Windows:

   `.venv\Scripts\Activate.ps1`

5. Install dependencies:

   `python -m pip install -r requirements.txt`

6. Create the database in MySQL:

   `CREATE DATABASE machine_risks_db;`

7. Create a MySQL user with the necessary permissions for that database.

8. Create a `.env` file in the project root with the following variables, using your own credentials:

   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=machine_risks_db
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   ```

9. Start the application:

   `python app.py`

10. Open `http://127.0.0.1:5000` in your browser.

The application creates the required tables and default machine fields on startup.

## Database Design

The `fields` table stores attribute definitions, including field name, label, type, required status and dropdown options.

The `machines` table stores machine records with their configurable attributes inside a MySQL JSON column.

Adding a custom field does not require an `ALTER TABLE` operation.

## Example: Adding Humidity

1. Open the field configuration section.
2. Enter `Humidity` as the field label.
3. Select `Number` as its type.
4. Leave it optional.
5. Save the field.

Humidity will appear in the machine form automatically. Existing machines can continue without a humidity value.

The current ML model does not use Humidity in its predictions. Adding new ML input features would require appropriate training data, model changes and validation.

## Risk Prediction

The local Random Forest classifier uses Temperature, Pressure and Vibration.

It predicts one of three categories:

- Low Risk
- Medium Risk
- High Risk

The model is trained on synthetic data generated from illustrative risk rules.

## Model Evaluation

Evaluation was performed using 300 separately generated synthetic samples.

| Metric | Result |
|---|---|
| Accuracy | 99.33% |
| Correct predictions | 298 |
| Incorrect predictions | 2 |

These metrics describe performance on synthetic examples generated from the same labeling rules used during training. They do not establish real-world industrial failure prediction performance.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/fields` | List field definitions |
| POST | `/api/fields` | Create a field |
| PUT | `/api/fields/<id>` | Edit a custom field |
| DELETE | `/api/fields/<id>` | Delete a custom field |
| GET | `/api/machines` | List machines |
| POST | `/api/machines` | Create a machine |
| PUT | `/api/machines/<id>` | Update a machine |
| DELETE | `/api/machines/<id>` | Delete a machine |
| POST | `/api/predict/<id>` | Predict machine risk |

## Testing

Run model tests:

`python -m pytest tests/test_model.py -v`

Run model evaluation:

`python -m ml.evaluate`

## Limitations and Future Improvements

- Synthetic training data rather than historical industrial sensor readings.
- Predictions are currently displayed in the browser rather than stored as historical results.
- Authentication, monitoring alerts and production deployment are outside the current scope.

## Security

Database credentials are read from environment variables. The `.env` file must not be committed to GitHub.