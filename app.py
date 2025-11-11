from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import joblib
import  numpy as np
model = joblib.load("drug_model.pkl")
le_sex, le_bp, le_chol = joblib.load("encoders.pkl")
import smtplib
from flask_mail import Mail, Message
from email.mime.text import MIMEText

def send_email(to_email, subject, message):
    try:
        sender_email = "youremail@gmail.com"
        sender_password = "your_app_password"

        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

from datetime import timedelta
from datetime import datetime


app = Flask(__name__)
app.secret_key = "your_secret_key"
app.permanent_session_lifetime = timedelta(minutes=30)

sex_map = {"Male": 1, "Female": 0}

bp_map = {
    "HIGH": 2,
    "NORMAL": 1,
    "LOW": 0
}

chol_map = {
    "HIGH": 2,
    "NORMAL": 1
}

# Load model
model = joblib.load("drug_model.pkl")



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "welcome":
            session.permanent = True
            session["user"] = username
            return redirect(url_for("form"))
        else:
            return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")

# Doctor Login route
@app.route("/doctor_login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Simple static login for doctor
        if username == "doctor" and password == "doctor123":
            session["doctor_logged_in"] = True
            return redirect(url_for("doctor_dashboard"))
        else:
            error = "Invalid username or password"
            return render_template("doctor_login.html", error=error)
    
    return render_template("doctor_login.html")


# Doctor Dashboard route
@app.route("/doctor_dashboard")
def doctor_dashboard():
    if not session.get("doctor_logged_in"):
        return redirect(url_for("doctor_login"))

    search_query = request.args.get("search", "").strip().lower()
    records = []
    try:
        with open("patient_history.csv", "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                
                # Skip header if present
                if row[0].lower() == "name":
                    continue

                # Search by name
                if search_query and search_query not in row[0].strip().lower():
                    continue

                rec = {
                    "name": row[0],
                    "email": row[1],
                    "phone": row[2],     # ✅ correct
                    "age": row[3],       # ✅ correct
                    "sex": row[4],
                    "bp": row[5],
                    "chol": row[6],
                    "sodium": row[7],
                    "potassium": row[8],
                    "sugar": row[9],
                    "pulse": row[10],
                    "bmi": row[11],
                    "prediction": row[12],
                    "date_time": row[13] if len(row) > 13 else ""
                }
                records.append(rec)

    except FileNotFoundError:
        pass

    records = sorted(records, key=lambda r: r["date_time"], reverse=True)

    return render_template("doctor_dashboard.html", records=records)
# show doctor-facing report page (GET)
@app.route("/doctor_view/<name>", methods=["GET"])
def doctor_view_report(name):
    name = name.strip()
    latest = None
    try:
        with open("patient_history.csv", "r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                if row[0].strip().lower() == name.lower():
                    latest = row  # keep last occurrence (latest)
    except FileNotFoundError:
        latest = None

    if not latest:
        flash("No record found for this patient.")
        return redirect(url_for("doctor_dashboard"))

    # ---- Flexible CSV parsing (support several formats) ----
    # Examples this function supports:
    # 1) [name, email, phone, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction, date_time, notes]
    # 2) [name, email, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction, date_time]
    # 3) older/simple: [name, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction, date_time]
    email = ""
    phone = ""
    age = ""
    sex = ""
    bp = ""
    chol = ""
    sodium = ""
    potassium = ""
    sugar = ""
    pulse = ""
    bmi = ""
    prediction = ""
    date_time = ""
    notes = ""

    L = len(latest)

    if L >= 14:
        # most-extended format (14+)
        email = latest[1]
        phone = latest[2]
        age = latest[3]
        sex = latest[4]
        bp = latest[5]
        chol = latest[6]
        sodium = latest[7]
        potassium = latest[8]
        sugar = latest[9]
        pulse = latest[10]
        bmi = latest[11]
        prediction = latest[12]
        date_time = latest[13]
        if L > 14:
            notes = latest[14]
    elif L == 13:
        # likely: name, email, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction, date_time
        email = latest[1]
        age = latest[2]
        sex = latest[3]
        bp = latest[4]
        chol = latest[5]
        sodium = latest[6]
        potassium = latest[7]
        sugar = latest[8]
        pulse = latest[9]
        bmi = latest[10]
        prediction = latest[11]
        date_time = latest[12]
    else:
        # fallback to the simple layout used previously
        # name at index 0, then age at 1, sex at 2, ...
        age = latest[1] if L > 1 else ""
        sex = latest[2] if L > 2 else ""
        bp = latest[3] if L > 3 else ""
        chol = latest[4] if L > 4 else ""
        sodium = latest[5] if L > 5 else ""
        potassium = latest[6] if L > 6 else ""
        sugar = latest[7] if L > 7 else ""
        pulse = latest[8] if L > 8 else ""
        bmi = latest[9] if L > 9 else ""
        prediction = latest[10] if L > 10 else ""
        date_time = latest[11] if L > 11 else ""
        notes = latest[12] if L > 12 else ""

    # ---- drug info dictionary (detailed) ----
    drug_info_dict = {
        'druga': {
            'name': 'Dolo-650 (Paracetamol)',
            'dose': '1 tablet, 3 times a day',
            'time': 'After food',
            'days': '3 days'
        },
        'drugb': {
            'name': 'Telma-40 (Telmisartan)',
            'dose': '1 tablet, once daily',
            'time': 'Morning before food',
            'days': '15 days'
        },
        'drugc': {
            'name': 'Metformin-500',
            'dose': '1 tablet, twice a day',
            'time': 'After breakfast and dinner',
            'days': '30 days'
        },
        'drugx': {
            'name': 'Atorva-10 (Atorvastatin)',
            'dose': '1 tablet, once at night',
            'time': 'After food',
            'days': '30 days'
        },
        'drugy': {
            'name': 'Amoxicillin-500',
            'dose': '1 tablet, 3 times a day',
            'time': 'After food',
            'days': '5 days'
        }
    }

    # lookup key case-insensitive; support variations like 'drugA','DrugA','druga'
    key = str(prediction).strip().lower() if prediction is not None else ""
    drug_info = drug_info_dict.get(key, {
        'name': str(prediction) or "Unknown",
        'dose': '',
        'time': '',
        'days': ''
    })

    # Finally render view (phone/email now available only here)
    return render_template(
        "doctor_view.html",
        name=latest[0],
        email=email,
        phone=phone,
        age=age,
        sex=sex,
        bp=bp,
        chol=chol,
        sodium=sodium,
        potassium=potassium,
        sugar=sugar,
        pulse=pulse,
        bmi=bmi,
        prediction=prediction,
        date_time=date_time,
        notes=notes,
        drug_info=drug_info
    )


@app.route("/doctor_save_notes", methods=["POST"])
def doctor_save_notes():
    patient_name = request.form.get("name")
    notes = request.form.get("notes", "").strip()

    # Read all rows and update the matching latest row for the patient
    rows = []
    updated = False
    try:
        with open("patient_history.csv", "r", newline="") as f:
            reader = list(csv.reader(f))
    except FileNotFoundError:
        reader = []

    # if header present, preserve it (optional)
    new_rows = []
    for row in reader:
        if not row:
            new_rows.append(row)
            continue
        # update the most recent entry matching the name
        if row[0].strip().lower() == patient_name.strip().lower() and not updated:
            # ensure row has space for notes
            if len(row) < 14:
                # extend to index 13 (0-based) for notes
                while len(row) < 14:
                    row.append("")
            row[13] = notes
            updated = True
        new_rows.append(row)

    if not updated:
        flash("Could not update notes (record not found).")
        return redirect(url_for("doctor_dashboard"))

    # write back
    with open("patient_history.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    flash("Doctor notes saved.")
    return redirect(url_for("doctor_view_report", name=patient_name))



@app.route("/doctor_logout")
def doctor_logout():
    session.pop("doctor_logged_in", None)
    return redirect(url_for("doctor_login"))


@app.route("/form")
def form():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("form.html")

def new_func(name, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction, csv_module):
    with open("patient_history.csv", "a", newline="") as f:
        writer = csv_module.writer(f)
        writer.writerow([name, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction])

@app.route("/predict", methods=["POST"])
def predict():
    try:
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form["phone"]
        sex_str = request.form.get("sex")
        bp_str = request.form.get("bp")
        chol_str = request.form.get("chol")

        age = float(request.form.get("age"))
        sodium = float(request.form.get("sodium"))
        potassium = float(request.form.get("potassium"))
        sugar = float(request.form.get("sugar"))
        pulse = float(request.form.get("PulseRate"))
        bmi = float(request.form.get("bmi"))

        sex_encoded = le_sex.transform([sex_str])[0]
        bp_encoded = le_bp.transform([bp_str])[0]
        chol_encoded = le_chol.transform([chol_str])[0]

        features = np.array([[sex_encoded, bp_encoded, chol_encoded, age, sodium, potassium, sugar, pulse, bmi]])

        prediction = model.predict(features)[0]

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("patient_history.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([name, email,phone,age, sex_str, bp_str, chol_str,
                             sodium, potassium, sugar, pulse, bmi, prediction, now])

        history = []
        with open("patient_history.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip().lower() == name.strip().lower():
                    history.append(row)

        drug_info_dict = {
    'drugA': {
        'name': 'Dolo-650 (Paracetamol)',
        'dose': '1 tablet, 3 times a day',
        'time': 'After food',
        'days': '3 days'
    },
    'drugB': {
        'name': 'Telma-40 (Telmisartan)',
        'dose': '1 tablet, once daily',
        'time': 'Morning before food',
        'days': '15 days'
    },
    'drugC': {
        'name': 'Metformin-500',
        'dose': '1 tablet, twice a day',
        'time': 'After breakfast and dinner',
        'days': '30 days'
    },
    'drugX': {
        'name': 'Atorva-10 (Atorvastatin)',
        'dose': '1 tablet, once at night',
        'time': 'After food',
        'days': '30 days'
    },
    'drugY': {
        'name': 'Amoxicillin-500',
        'dose': '1 tablet, 3 times a day',
        'time': 'After food',
        'days': '5 days'
    }
}


        drug_info = drug_info_dict.get(prediction, {
    'name': prediction,
    'dose': 'Not available',
    'time': 'Not available',
    'days': 'Not available'
})

        return render_template("result.html", name=name, email=email,phone=phone,age=age, sex=sex_str,
                               bp=bp_str, chol=chol_str, sodium=sodium, potassium=potassium,
                               sugar=sugar, pulse=pulse, bmi=bmi, prediction=prediction,
                               history=history, drug_info=drug_info)

    except Exception as e:
        return f"Prediction failed: {e}", 400


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

def new_func(name,email, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction, csv_module):
    try:
        rows = []
        found = False

        # Read existing rows
        with open("patient_history.csv", "r") as f:
            reader = csv_module.reader(f)
            for row in reader:
                if row[0] == name and row[1] == str(age):
                    found = True
                else:
                    rows.append(row)

        # Add new/updated row
        rows.append([name, email, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction])

        # Rewrite the file
        with open("patient_history.csv", "w", newline="") as f:
            writer = csv_module.writer(f)
            writer.writerows(rows)

    except FileNotFoundError:
        # File doesn't exist yet, create and write the first row
        with open("patient_history.csv", "w", newline="") as f:
            writer = csv_module.writer(f)
            writer.writerow([name, age, sex, bp, chol, sodium, potassium, sugar, pulse, bmi, prediction])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

