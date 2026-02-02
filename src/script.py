from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your HTML frontend

@app.route("/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith(".csv"):
        return jsonify({"error": "File is not a CSV"}), 400

    # Read CSV with pandas
    df = pd.read_csv(file)

    # For demonstration, print first 5 rows
    print("Received CSV:")
    print(df.head())

    return jsonify({"message": f"CSV received: {file.filename}", "rows": len(df)}), 200

if __name__ == "__main__":
    app.run(debug=True)
