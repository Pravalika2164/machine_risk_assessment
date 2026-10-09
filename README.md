# Dynamic Machine Data Management & Local Risk Prediction

A full-stack machine management application developed using Python, Flask, MySQL, JavaScript, and scikit-learn. It supports configurable machine attributes, dynamically generated forms, CRUD operations, and local machine risk prediction using a Random Forest classifier.

## Features

- Create configurable machine fields with text, number, and dropdown types.
- Edit and delete custom fields.
- Automatically generate machine forms based on configured attributes.
- Add, view, edit, and delete machine records.
- Store flexible machine attributes using MySQL JSON columns.
- Add optional fields such as Humidity without changing the database schema.
- Predict Low, Medium, or High Risk using a local Random Forest classifier.
- Validate required fields, numeric values, and dropdown selections.
- Normalize numeric inputs before storing new or updated machine records.
- Protect core machine attributes required by the prediction model.
- Responsive browser-based dashboard.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | scikit-learn, NumPy |
| ML Algorithm | Random Forest Classifier |
| Testing | pytest |
| Configuration | python-dotenv |

## System Architecture

The application follows a local full-stack architecture:

Browser (HTML, CSS, JavaScript)
â†“
Flask REST API (`app.py`)
â†“
MySQL database (`fields`, `machines`) and local ML model (`ml/model.py`)
â†“
Flask API response
â†“
Browser dashboard

**Application workflow:**

1. Users configure machine attributes through the web interface.
2. Flask receives API requests and validates submitted information.
3. MySQL stores field definitions and machine records.
4. Users request risk predictions for individual machines.
5. Flask retrieves the machine's attributes from MySQL.
6. The local Random Forest model processes Temperature, Pressure, and Vibration.
7. Flask returns the predicted risk category to the browser.

The ML model is trained automatically when the application imports `ml/model.py`. It runs within the Flask process and does not require a separate machine learning server or external prediction API.

## Installation and Setup

### Prerequisites

- Python 3 (tested with Python 3.14.3)
- A running MySQL server
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/Pravalika2164/machine_risk_assessment.git
cd machine_risk_assessment
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Create the MySQL database

Log in to MySQL and execute:

```sql
CREATE DATABASE IF NOT EXISTS machine_risks_db;
```

Create a dedicated database user if needed:

```sql
CREATE USER IF NOT EXISTS 'machine_app'@'localhost'
IDENTIFIED BY 'replace_with_a_secure_password';

GRANT ALL PRIVILEGES ON machine_risks_db.*
TO 'machine_app'@'localhost';
```

Use your own secure password. These commands are intended for initial setup by an account with the required MySQL privileges.

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=machine_risks_db
DB_USER=machine_app
DB_PASSWORD=your_mysql_password
```

Replace the example values with your actual database credentials.

The `.env` file is excluded from Git using `.gitignore`.

### 6. Start the application

```bash
python app.py
```

Open the application in your browser:

http://127.0.0.1:5000

The application automatically creates the required tables and initializes the default machine fields during startup.

## Database Design

The application uses two MySQL tables.

### fields

Stores configurable attribute definitions, including:

- Field name
- Display label
- Data type
- Required or optional status
- Dropdown options
- Creation timestamp

### machines

Stores machine records, including:

- Unique machine ID
- Machine attributes in a JSON column
- Creation timestamp
- Last updated timestamp

The JSON-based design allows new machine attributes to be introduced without modifying the database table structure.

## Database Schema

The complete table definitions are provided in [`schema.sql`](schema.sql).

The application creates the tables and initializes default fields automatically when started using `python app.py`. Running `schema.sql` manually is optional.

Default machine fields:

| Field | Type | Required |
|---|---|---|
| Machine Name | Text | Yes |
| Temperature | Number | Yes |
| Pressure | Number | Yes |
| Vibration | Dropdown | Yes |

Vibration supports `Low`, `Medium`, and `High`.

Core fields are protected from deletion or incompatible modification because the risk prediction model depends on their structure and expected values.

## Dynamic Field Management

Users can create additional machine attributes through the field configuration interface.

Supported field types:

- **Text:** Textual values.
- **Number:** Numeric measurements.
- **Dropdown:** Selection from predefined options.

Fields can be configured as required or optional, subject to compatibility with existing records.

The application validates machine data against the configured field definitions.

Numeric strings such as `"85"` are converted to numeric values before newly created or updated machine records are stored.

Boolean values are rejected for numeric fields. Required text fields cannot contain only whitespace, and surrounding whitespace is removed from text values.

## Example: Adding Humidity

The application demonstrates how optional machine attributes can be added without changing the MySQL schema.

### Steps

1. Open the field configuration section.
2. Enter `Humidity` as the field label.
3. Select `Number` as the field type.
4. Leave the field optional.
5. Save the new field.

Humidity automatically appears in the machine creation and editing forms.

Existing machines can remain valid without a Humidity value.

### Impact on Machine Learning

The current prediction model uses only:

- Temperature
- Pressure
- Vibration

Humidity is stored as a configurable machine attribute but is not used by the current prediction model.

**Retraining for Humidity is not part of the current implementation.**

To incorporate Humidity into future predictions, the following changes would be required:

1. Collect appropriate training data containing Humidity measurements and corresponding risk labels.
2. Add `humidity` to the model's feature configuration.
3. Handle missing Humidity values because the field is optional.
4. Update model preprocessing and training logic.
5. Retrain the model using the expanded feature set.
6. Evaluate the updated model on separate test data.
7. Version the updated model and document its performance.

This design separates flexible machine data storage from the specific features used for machine learning.

## Risk Prediction

The application uses a local Random Forest classifier implemented with scikit-learn.

### Input Features

| Feature | Description |
|---|---|
| Temperature | Machine temperature |
| Pressure | Machine pressure |
| Vibration | Low, Medium, or High vibration level |

### Prediction Categories

- Low Risk
- Medium Risk
- High Risk

The model is trained using synthetic machine readings and illustrative risk-labeling rules.

Categorical vibration values are processed using one-hot encoding.

The prediction model runs locally without an external machine learning API.

### Assessment Example

Input:

```json
{
  "temperature": 85,
  "pressure": 120,
  "vibration": "High"
}
```

Expected prediction:

```text
High Risk
```

This example is verified by an automated regression test.

## Model Evaluation

The updated Random Forest model was evaluated using 300 separately generated synthetic samples.

### Evaluation Results

| Metric | Result |
|---|---|
| Accuracy | 95.00% |
| Correct predictions | 285 |
| Incorrect predictions | 15 |
| Evaluation samples | 300 |

### Classification Report

| Risk Category | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| Low Risk | 1.00 | 0.99 | 0.99 | 80 |
| Medium Risk | 0.99 | 0.91 | 0.95 | 152 |
| High Risk | 0.84 | 0.99 | 0.91 | 68 |
| **Weighted Average** | **0.96** | **0.95** | **0.95** | **300** |

### Confusion Matrix

```text
[[ 79   1   0]
 [  0 139  13]
 [  0   1  67]]
```

Class order:

```text
['Low Risk', 'Medium Risk', 'High Risk']
```

Run model evaluation:

```bash
python -m ml.evaluate
```

**Evaluation limitation:** These metrics describe performance on synthetic examples generated using the same illustrative labeling rules used during training. They do not establish real-world industrial failure prediction performance.

The model demonstrates local machine learning integration rather than production-ready predictive maintenance.

## API Endpoints

### Field Management

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/fields` | Retrieve field definitions |
| POST | `/api/fields` | Create a custom field |
| PUT | `/api/fields/<id>` | Update a custom field |
| DELETE | `/api/fields/<id>` | Delete a custom field |

### Machine Management

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/machines` | Retrieve machine records |
| POST | `/api/machines` | Create a machine |
| PUT | `/api/machines/<id>` | Update a machine |
| DELETE | `/api/machines/<id>` | Delete a machine |

### Risk Prediction

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/predict/<id>` | Predict risk for a machine |

The prediction endpoint retrieves the machine record, extracts the required model features, and returns the predicted risk category.

## Testing

The project includes **29 automated tests** using pytest.

### Flask API and Validation Tests â€” 24

Tests cover:

- Home page response
- Field retrieval and creation
- Machine CRUD operations
- Required-field validation
- Invalid numeric input handling
- Numeric string conversion
- Boolean rejection for numeric fields
- Whitespace-only required text rejection
- Invalid dropdown selections
- Unknown field rejection
- Invalid JSON handling
- Custom field management
- Core-field protection
- Risk prediction endpoints
- Missing machine and missing feature handling

These tests use mocked field definitions and database access where applicable. They do not modify a real MySQL database.

### Machine Learning Tests â€” 5

Tests cover:

- Valid risk prediction categories
- Prediction repeatability
- The assessment's High Risk example

The regression test verifies:

```text
Temperature = 85
Pressure = 120
Vibration = High

Expected prediction: High Risk
```

### Run All Tests

```bash
python -m pytest -v
```

Latest test result:

```text
29 passed in 1.39s
```

### Run Model Evaluation

```bash
python -m ml.evaluate
```

## Security and Validation

The application includes the following safeguards:

- Database credentials are loaded from environment variables.
- The `.env` file is excluded from version control.
- SQL statements use parameterized queries for user-provided values.
- Machine attributes are validated against configured field definitions.
- Numeric strings are normalized before saving.
- Boolean values are rejected for numeric fields.
- Required text values cannot contain only whitespace.
- Dropdown values are checked against configured options.
- Core fields used by the ML model are protected.
- Flask binds to localhost by default.
- Debug mode is disabled by default.

The application is designed as a local assessment prototype and does not include production authentication or authorization.

## Limitations and Future Improvements

- The ML model uses synthetic training data rather than historical industrial sensor readings.
- Predictions are displayed in the browser rather than stored as historical results.
- The model currently uses only Temperature, Pressure, and Vibration.
- Incorporating additional ML features requires suitable data, preprocessing changes, retraining, and evaluation.
- Automated API tests mock database access; dedicated MySQL integration tests could be added.
- Authentication, monitoring alerts, and production deployment are outside the current scope.

Potential future improvements include:

- Training with real machine sensor datasets.
- Incorporating Humidity and additional sensor measurements.
- Saving prediction history.
- Adding monitoring alerts and model performance tracking.
- Adding automated integration tests using a dedicated test database.

## Project Purpose

This project demonstrates:

- Full-stack development using Flask and JavaScript.
- Dynamic database-driven forms and configurable attributes.
- JSON-based data storage in MySQL.
- REST API development and input validation.
- Local machine learning integration using scikit-learn.
- Automated testing and model evaluation.

The implementation focuses on meeting the assessment requirements through a functional local application with extensible machine attributes and risk prediction capabilities.
