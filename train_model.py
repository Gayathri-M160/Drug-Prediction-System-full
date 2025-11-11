import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
import joblib

df = pd.read_csv("drug_data.csv")

# Encode categorical fields
le_sex = LabelEncoder()
le_bp = LabelEncoder()
le_chol = LabelEncoder()

df["Sex"] = le_sex.fit_transform(df["Sex"])
df["BP"] = le_bp.fit_transform(df["BP"])
df["Cholesterol"] = le_chol.fit_transform(df["Cholesterol"])

# Correct input order
X = df[["Sex","BP","Cholesterol","Age","Sodium","Potassium","Sugar","PulseRate","BMI"]]
y = df["Drug"]

# Train model
model = DecisionTreeClassifier()
model.fit(X, y)

joblib.dump(model, "drug_model.pkl")
joblib.dump((le_sex, le_bp, le_chol), "encoders.pkl")

print("✅ MODEL TRAINED SUCCESSFULLY ✅")
