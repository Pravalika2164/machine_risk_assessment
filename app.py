
import json
import os
import re
from contextlib import contextmanager

import mysql.connector
from mysql.connector import IntegrityError
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from ml.model import predict, FEATURES


# --------------------------------------------------
# 1. APPLICATION CONFIGURATION
# --------------------------------------------------

load_dotenv()

app = Flask(__name__)

CORE_FIELDS = {
    "machine_name",
    "temperature",
    "pressure",
    "vibration",
}

VALID_FIELD_TYPES = {"text", "number", "dropdown"}


# --------------------------------------------------
# 2. DATABASE CONNECTION
# --------------------------------------------------

def connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "machine_risks_db"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


@contextmanager
def db_cursor():
    db = connection()
    cursor = None

    try:
        cursor = db.cursor(dictionary=True)
        yield cursor
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        db.close()


# --------------------------------------------------
# 3. DATABASE INITIALIZATION
# --------------------------------------------------

def init_db():
    with db_cursor() as cursor:

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fields (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                label VARCHAR(100) NOT NULL,
                type ENUM('text', 'number', 'dropdown') NOT NULL,
                required BOOLEAN NOT NULL DEFAULT FALSE,
                options JSON NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS machines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM fields"
        )

        count = cursor.fetchone()["total"]

        if count == 0:
            defaults = [
                (
                    "machine_name",
                    "Machine Name",
                    "text",
                    1,
                    "[]",
                ),
                (
                    "temperature",
                    "Temperature",
                    "number",
                    1,
                    "[]",
                ),
                (
                    "pressure",
                    "Pressure",
                    "number",
                    1,
                    "[]",
                ),
                (
                    "vibration",
                    "Vibration",
                    "dropdown",
                    1,
                    '["Low", "Medium", "High"]',
                ),
            ]

            cursor.executemany("""
                INSERT INTO fields
                (name, label, type, required, options)
                VALUES (%s, %s, %s, %s, %s)
            """, defaults)


# --------------------------------------------------
# 4. FETCH DYNAMIC FIELD DEFINITIONS
# --------------------------------------------------

def fields():
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT * FROM fields ORDER BY id"
        )

        rows = cursor.fetchall()

    result = []

    for row in rows:
        row["required"] = bool(row["required"])

        row["options"] = json.loads(
            row["options"] or "[]"
        )

        row.pop("created_at", None)

        result.append(row)

    return result


# --------------------------------------------------
# 5. VALIDATION HELPERS
# --------------------------------------------------

def valid_dropdown_options(options):
    return (
        isinstance(options, list)
        and bool(options)
        and all(
            isinstance(option, str) and option.strip()
            for option in options
        )
        and len(set(options)) == len(options)
    )



def validate(data):
    if not isinstance(data, dict):
        return "Expected a JSON object"

    configured_fields = fields()

    allowed_names = {
        field["name"] for field in configured_fields
    }

    if set(data) - allowed_names:
        return "Unknown fields are not allowed"

    for field in configured_fields:
        name = field["name"]
        label = field["label"]
        value = data.get(name)

        if field["type"] == "text" and isinstance(value, str):
            value = value.strip()
            data[name] = value

        if field["required"] and (
            value is None or value == ""
        ):
            return f"{label} is required"

        if value is None or value == "":
            continue

        if field["type"] == "number":
            if isinstance(value, bool):
                return f"{label} must be a valid number"

            try:
                number = float(value)

                if not (-1e12 < number < 1e12):
                    raise ValueError()

                data[name] = number

            except (ValueError, TypeError, OverflowError):
                return f"{label} must be a valid number"

        elif field["type"] == "dropdown":
            if not isinstance(value, str) or value not in field["options"]:
                return f"{label} must match a dropdown option"

        elif field["type"] == "text":
            if not isinstance(value, str):
                return f"{label} must be text"

    return None



# --------------------------------------------------
# 6. HOME PAGE
# --------------------------------------------------

@app.get("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# 7. DYNAMIC FIELD CREATE / READ API
# --------------------------------------------------

@app.route("/api/fields", methods=["GET", "POST"])
def field_api():

    if request.method == "GET":
        return jsonify(fields())

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="Expected a JSON object"
        ), 400

    label = str(
        data.get("label", "")
    ).strip()

    name = re.sub(
        r"[^a-z0-9]+",
        "_",
        label.lower(),
    ).strip("_")

    field_type = data.get("type")
    options = data.get("options", [])
    required = bool(data.get("required", False))

    if (
        not name
        or len(label) > 80
        or field_type not in VALID_FIELD_TYPES
    ):
        return jsonify(
            error="Provide a field name and valid type"
        ), 400

    if name in CORE_FIELDS:
        return jsonify(
            error="Core fields already exist"
        ), 409

    if field_type == "dropdown":
        if not valid_dropdown_options(options):
            return jsonify(
                error=(
                    "Dropdown needs unique, "
                    "nonempty options"
                )
            ), 400

    else:
        options = []

    try:
        with db_cursor() as cursor:

            # IMPORTANT FIX:
            # Existing machines cannot automatically
            # provide values for a new required field.
            #
            # Prevent adding a required field if
            # machine records already exist.

            if required:
                cursor.execute(
                    "SELECT COUNT(*) AS total FROM machines"
                )

                total = cursor.fetchone()["total"]

                if total > 0:
                    return jsonify(
                        error=(
                            "Cannot create a required field "
                            "while machines already exist. "
                            "Create the field as optional first, "
                            "fill the values in existing machines, "
                            "then edit the field to make it required."
                        )
                    ), 409

            cursor.execute("""
                INSERT INTO fields
                (name, label, type, required, options)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                name,
                label,
                field_type,
                int(required),
                json.dumps(options),
            ))

    except IntegrityError:
        return jsonify(
            error="Field already exists"
        ), 409

    return jsonify(fields()), 201


# --------------------------------------------------
# 8. MACHINE CREATE / READ API
# --------------------------------------------------

@app.route("/api/machines", methods=["GET", "POST"])
def machine_api():

    if request.method == "GET":

        with db_cursor() as cursor:
            cursor.execute("""
                SELECT id, data
                FROM machines
                ORDER BY id DESC
            """)

            rows = cursor.fetchall()

        machines = [
            {
                "id": row["id"],
                "data": json.loads(row["data"]),
            }
            for row in rows
        ]

        return jsonify(machines)

    data = request.get_json(silent=True)

    error = validate(data)

    if error:
        return jsonify(error=error), 400

    with db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO machines (data) VALUES (%s)",
            (json.dumps(data),),
        )

        machine_id = cursor.lastrowid

    return jsonify(
        id=machine_id,
        data=data,
    ), 201


# --------------------------------------------------
# 9. MACHINE UPDATE / DELETE API
# --------------------------------------------------

@app.route(
    "/api/machines/<int:machine_id>",
    methods=["PUT", "DELETE"],
)
def machine_detail(machine_id):

    data = None

    if request.method == "PUT":

        data = request.get_json(silent=True)

        error = validate(data)

        if error:
            return jsonify(error=error), 400

    with db_cursor() as cursor:

        cursor.execute(
            "SELECT id FROM machines WHERE id = %s",
            (machine_id,),
        )

        if cursor.fetchone() is None:
            return jsonify(
                error="Machine not found"
            ), 404

        if request.method == "DELETE":

            cursor.execute(
                "DELETE FROM machines WHERE id = %s",
                (machine_id,),
            )

        else:
            cursor.execute("""
                UPDATE machines
                SET data = %s
                WHERE id = %s
            """, (
                json.dumps(data),
                machine_id,
            ))

    return jsonify(success=True)


# --------------------------------------------------
# 10. MACHINE RISK PREDICTION API
# --------------------------------------------------

@app.post("/api/predict/<int:machine_id>")
def risk(machine_id):

    with db_cursor() as cursor:
        cursor.execute(
            "SELECT data FROM machines WHERE id = %s",
            (machine_id,),
        )

        row = cursor.fetchone()

    if row is None:
        return jsonify(
            error="Machine not found"
        ), 404

    data = json.loads(row["data"])

    try:
        if any(
            data.get(key) in (None, "")
            for key in FEATURES
        ):
            return jsonify(
                error=(
                    "Temperature, pressure and vibration "
                    "are required for prediction"
                )
            ), 400

        risk_level = predict(data)

    except (ValueError, TypeError, KeyError) as error:
        return jsonify(
            error=f"Invalid prediction inputs: {error}"
        ), 400

    return jsonify(
        machine_id=machine_id,
        risk=risk_level,
        features_used=FEATURES,
        ignored_fields=[
            key
            for key in data
            if key not in FEATURES
        ],
    )


# --------------------------------------------------
# 11. EDIT / DELETE CUSTOM FIELDS
# --------------------------------------------------

@app.route(
    "/api/fields/<int:field_id>",
    methods=["PUT", "DELETE"],
)
def field_detail(field_id):

    with db_cursor() as cursor:

        cursor.execute(
            "SELECT * FROM fields WHERE id = %s",
            (field_id,),
        )

        field = cursor.fetchone()

        if field is None:
            return jsonify(
                error="Field not found"
            ), 404

        if field["name"] in CORE_FIELDS:
            return jsonify(
                error=(
                    "Core machine fields cannot "
                    "be edited or deleted"
                )
            ), 403

        # ------------------------------------------
        # DELETE CUSTOM FIELD
        # ------------------------------------------

        if request.method == "DELETE":

            json_path = (
                '$."' + field["name"] + '"'
            )

            cursor.execute("""
                UPDATE machines
                SET data = JSON_REMOVE(data, %s)
                WHERE JSON_CONTAINS_PATH(
                    data, 'one', %s
                )
            """, (
                json_path,
                json_path,
            ))

            cursor.execute(
                "DELETE FROM fields WHERE id = %s",
                (field_id,),
            )

            return jsonify(success=True)

        # ------------------------------------------
        # EDIT CUSTOM FIELD
        # ------------------------------------------

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify(
                error="Expected a JSON object"
            ), 400

        label = str(
            data.get("label", field["label"])
        ).strip()

        field_type = data.get(
            "type",
            field["type"],
        )

        required = bool(
            data.get(
                "required",
                field["required"],
            )
        )

        if not label or len(label) > 80:
            return jsonify(
                error="Invalid field label"
            ), 400

        if field_type not in VALID_FIELD_TYPES:
            return jsonify(
                error="Invalid field type"
            ), 400

        options = data.get("options")

        if options is None:
            options = json.loads(
                field["options"] or "[]"
            )

        if field_type == "dropdown":

            if not valid_dropdown_options(options):
                return jsonify(
                    error=(
                        "Dropdown requires unique, "
                        "nonempty options"
                    )
                ), 400

        else:
            options = []

        # ------------------------------------------
        # CHECK EXISTING MACHINE RECORDS
        # ------------------------------------------

        cursor.execute(
            "SELECT id, data FROM machines"
        )

        machines = cursor.fetchall()

        for machine in machines:

            saved = json.loads(
                machine["data"]
            )

            value = saved.get(
                field["name"]
            )

            if value is None or value == "":

                if required:
                    return jsonify(
                        error=(
                            f"Machine {machine['id']} has "
                            f"no value for {field['label']}. "
                            "Fill existing records before "
                            "making this field required."
                        )
                    ), 409

                continue

            if field_type == "number":

                try:
                    number = float(value)

                    if not (-1e12 < number < 1e12):
                        raise ValueError()

                except (
                    TypeError,
                    ValueError,
                    OverflowError,
                ):
                    return jsonify(
                        error=(
                            f"Machine {machine['id']} "
                            "has an invalid number"
                        )
                    ), 409

            elif field_type == "text":

                if not isinstance(value, str):
                    return jsonify(
                        error=(
                            f"Machine {machine['id']} "
                            "has a non-text value"
                        )
                    ), 409

            elif field_type == "dropdown":

                if value not in options:
                    return jsonify(
                        error=(
                            f"Machine {machine['id']} "
                            "has a value not present in "
                            "the new dropdown options"
                        )
                    ), 409

        # ------------------------------------------
        # UPDATE FIELD CONFIGURATION
        # ------------------------------------------

        cursor.execute("""
            UPDATE fields
            SET label = %s,
                type = %s,
                required = %s,
                options = %s
            WHERE id = %s
        """, (
            label,
            field_type,
            int(required),
            json.dumps(options),
            field_id,
        ))

    return jsonify(
        success=True,
        fields=fields(),
    )


# --------------------------------------------------
# 12. START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
