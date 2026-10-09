
# Dynamic Machine Data Management & Local Risk Prediction

A full-stack web application for managing machine records with dynamically configurable fields and predicting machine risk levels using a locally trained Machine Learning model.

The application uses Flask, MySQL, JavaScript, and scikit-learn. It supports machine CRUD operations, flexible field definitions, input validation, and risk predictions without relying on external prediction APIs.

## Features

- Create, view, update, and delete machine records.
- Add and manage dynamic machine fields.
- Store flexible machine attributes using MySQL JSON.
- Generate input forms based on field definitions.
- Validate required fields and numeric inputs.
- Predict machine risk as Low Risk, Medium Risk, or High Risk.
- Run the Machine Learning model locally.
- Evaluate the model using a separate synthetic dataset.
- Test application behavior using pytest.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | scikit-learn, NumPy |
| ML Algorithm | Random Forest Classifier |
| Testing | pytest |
| Configuration | Environment variables |

## System Architecture

The application follows this workflow:

1. Users interact with the web interface.
2. JavaScript communicates with the Flask backend.
3. Flask validates requests and performs database operations.
4. MySQL stores field definitions and machine records.
5. The local Machine Learning model generates risk predictions.
6. Prediction results are returned to the user interface.

```text
             User
              |
              v
     HTML / CSS / JavaScript
              |
              v
         Flask Backend
          /         \
         v           v
   MySQL Database   Local ML Model
         |           |
         v           v
   Machine Records  Risk Prediction
```

## Project Structure

```text
machine-risk-assessment/
|
|-- app.py
|-- schema.sql
|-- requirements.txt
|-- README.md
|-- .gitignore
|
|-- ml/
|   |-- model.py
|   |-- evaluate.py
|
|-- tests/
|   |-- test_app.py
|   |-- test_model.py
|
|-- templates/
|   |-- index.html
|
|-- static/
|   |-- css/
|   |-- js/
```

The project also uses a local `.env` file for configuration. This file should not be committed to GitHub.

## Database Design

The application uses a MySQL database named:

`machine_risks_db`

It contains two main tables:

### 1. fields

Stores the definitions of machine attributes.

Field definitions determine which inputs are available in the machine form, including their names, data types, and validation requirements.

### 2. machines

Stores machine records and their associated attributes.

Machine attributes are stored using a JSON column, allowing records to contain flexible sets of fields without requiring a database schema change for every new attribute.

### Why JSON Storage?

Traditional relational tables require fixed columns.

By storing machine attributes as JSON, the application can support additional fields without repeatedly altering the machines table.

The database structure is documented in `schema.sql`.

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Pravalika2164/machine_risk_assessment.git
cd machine_risk_assessment
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Ensure MySQL Server is installed and running.

Create the database and required tables using the SQL definitions provided in `schema.sql`.

For a fresh database, you can import the schema using:

```bash
mysql -u root -p < schema.sql
```

Review the SQL script before running it against an existing database.

### 5. Configure Environment Variables

Create a `.env` file in the project root.

Configure the MySQL connection values expected by `app.py`.

Do not commit `.env` to version control because it may contain database credentials.

### 6. Start the Application

```bash
python app.py
```

Open the local address displayed by Flask in your browser.

## Dynamic Field Management

Machine attributes are configured using field definitions rather than hard-coded database columns.

The application supports a workflow where:

1. A field definition is created.
2. The frontend retrieves the available field definitions.
3. The machine form is generated using those definitions.
4. Submitted values are validated by the backend.
5. Machine data is stored in MySQL as JSON.

For example, a new field named `humidity` can be introduced without adding a separate humidity column to the machines table.

This makes the data-management layer more flexible as requirements change.

## Machine Record Management

The application provides CRUD functionality:

- **Create:** Add a machine with its configured attributes.
- **Read:** Retrieve stored machine records.
- **Update:** Modify existing machine information.
- **Delete:** Remove machine records.

Backend validation helps prevent invalid data from being stored.

Numeric inputs are normalized to numeric values, and required text fields cannot contain only whitespace.

## Local Machine Learning Model

The project uses a Random Forest Classifier implemented with scikit-learn.

The model is trained locally using synthetic machine operating conditions.

### Input Features

| Feature | Description |
|---|---|
| temperature | Numeric machine temperature |
| pressure | Numeric machine pressure |
| vibration | Categorical vibration level: Low, Medium, High |

### Output Classes

The model predicts one of three risk levels:

- Low Risk
- Medium Risk
- High Risk

### Training Approach

The training dataset contains 1,200 synthetically generated samples.

The data is generated using a fixed random seed to support reproducibility.

The synthetic risk labels are determined using a scoring system based on temperature, pressure, and vibration.

The scoring logic is:

| Condition | Score |
|---|---:|
| Temperature greater than 75 | +1 |
| Temperature greater than 95 | +1 |
| Pressure greater than 130 | +1 |
| Pressure greater than 165 | +1 |
| Vibration = Medium | +1 |
| Vibration = High | +3 |

The final risk classification is:

| Total Score | Risk Level |
|---|---|
| 0–1 | Low Risk |
| 2–3 | Medium Risk |
| 4 or above | High Risk |

These thresholds are illustrative rules used to generate synthetic labels. They are not validated industrial safety thresholds.

### Model Pipeline

The Machine Learning pipeline includes:

1. One-hot encoding of the categorical vibration feature.
2. Passing numerical features to the classifier.
3. Training a Random Forest Classifier.
4. Predicting the machine's risk level.

The classifier uses:

- 90 decision trees
- Random state: 42
- Minimum samples per leaf: 2

The trained model is created locally when the model module is loaded.

## Example Prediction

Consider the following machine readings:

```json
{
  "temperature": 85,
  "pressure": 120,
  "vibration": "High"
}
```

The synthetic scoring rules assign:

- Temperature greater than 75: +1
- Temperature greater than 95: +0
- Pressure greater than 130: +0
- Pressure greater than 165: +0
- High vibration: +3

Total score: 4

Expected risk according to the synthetic labeling rules:

**High Risk**

A regression test verifies that the local model predicts High Risk for this assessment example.

## Model Evaluation

The model was evaluated on a separate synthetic dataset containing 300 samples.

The evaluation uses a different random seed from the training dataset and follows the same synthetic labeling rules.

Run the evaluation using:

```bash
python -m ml.evaluate
```

### Evaluation Results

| Metric | Result |
|---|---:|
| Evaluation samples | 300 |
| Accuracy | 99.33% |
| Correct predictions | 298 |
| Incorrect predictions | 2 |

### Classification Report

| Risk Level | Precision | Recall | F1-score | Support |
|---|---:|---:|---:|---:|
| Low Risk | 1.00 | 0.99 | 0.99 | 80 |
| Medium Risk | 0.99 | 1.00 | 0.99 | 139 |
| High Risk | 1.00 | 0.99 | 0.99 | 81 |

### Confusion Matrix

| Actual / Predicted | Low Risk | Medium Risk | High Risk |
|---|---:|---:|---:|
| Low Risk | 79 | 1 | 0 |
| Medium Risk | 0 | 139 | 0 |
| High Risk | 0 | 1 | 80 |

The model correctly classified 298 of the 300 evaluation samples.

**Important:** These results measure performance against synthetically generated labels. They do not demonstrate the model's accuracy on real-world industrial equipment or actual machine failures.

## Automated Testing

The project includes automated tests for application behavior and Machine Learning predictions.

Run all tests using:

```bash
python -m pytest -q
```

### Final Test Results

```text
.............................                            [100%]
29 passed in 1.32s
```

The tests cover machine-management behavior, input validation, prediction behavior, and a regression case for the assessment's High Risk example.

The API tests use mocked database interactions, allowing them to run without modifying production or existing MySQL records.

## Error Handling and Validation

The application validates incoming machine data before storing it.

Validation includes:

- Checking required fields.
- Rejecting missing required values.
- Rejecting whitespace-only required text values.
- Validating numeric fields.
- Rejecting boolean values where numeric values are expected.
- Converting valid numeric input strings to numbers.

This improves consistency between frontend inputs and stored machine attributes.

## Design Decisions

### Dynamic Fields Instead of Fixed Columns

Field definitions allow the application to evolve without a database migration for every new machine attribute.

### MySQL JSON for Machine Attributes

JSON storage provides flexibility while preserving relational database support for core records.

### Local Prediction Instead of External APIs

The Machine Learning model runs locally, so risk predictions do not require an external ML service.

### Random Forest Classifier

Random Forest provides a straightforward approach for classifying machine readings using numerical and categorical features.

### Synthetic Dataset

Synthetic data makes the demonstration reproducible when real machine datasets are unavailable.

## Limitations

- The Machine Learning model is trained and evaluated using synthetic data.
- Risk labels are generated from predefined scoring rules rather than real machine failure records.
- The reported accuracy should not be interpreted as real-world failure prediction accuracy.
- The prediction model currently uses only temperature, pressure, and vibration.
- Additional dynamic fields can be stored, but they do not automatically become Machine Learning features.
- Real industrial deployment would require validated operational data, monitoring, and further model evaluation.

## Future Improvements

Potential improvements include:

- Training with real historical machine and failure data.
- Adding additional sensor features.
- Supporting configurable Machine Learning features.
- Adding model versioning and persistence.
- Improving monitoring and operational reporting.
- Expanding integration and end-to-end testing.

## Conclusion

This project demonstrates a complete workflow for managing flexible machine data and generating local Machine Learning predictions.

It combines dynamic field management, MySQL JSON storage, Flask-based backend operations, frontend interaction, input validation, and a reproducible Random Forest evaluation.

The final synthetic evaluation achieved **99.33% accuracy**, and **all 29 automated tests passed**.
