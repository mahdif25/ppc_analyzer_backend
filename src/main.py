import os
import sys
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np # Added for type checking
import logging
from werkzeug.utils import secure_filename
import chardet # For robust encoding detection

# Assuming analysis_engine.py and recommendation_engine.py are in the same directory (src)
from analysis_engine import MetricsAnalysisEngine
from recommendation_engine import RecommendationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure the path for sys.path.insert is correct relative to where main.py is
# If main.py is in /home/ubuntu/ppc_analyzer_backend/src, then its parent is /home/ubuntu/ppc_analyzer_backend
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# Corrected path insertion based on typical Flask project structure where main.py is in src/
# and modules like analysis_engine are also in src/ or subdirectories.
# If analysis_engine and recommendation_engine are in the same dir as main.py, this isn't strictly needed
# but doesn't hurt if they are treated as part of a package.

UPLOAD_FOLDER = ".uploads"
ALLOWED_EXTENSIONS = {"csv"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to convert NumPy types to native Python types for JSON serialization
def convert_numpy_types_to_native(obj):
    if isinstance(obj, dict):
        return {k: convert_numpy_types_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types_to_native(elem) for elem in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat() # Convert Timestamp to ISO string
    return obj

@app.route("/upload_ppc_reports", methods=["POST"])
def upload_ppc_reports():
    if "files[]" not in request.files:
        logger.warning("No file part in request")
        return jsonify({"error": "No file part"}), 400
    
    files = request.files.getlist("files[]")
    
    if not files or all(file.filename == "" for file in files):
        logger.warning("No selected files")
        return jsonify({"error": "No selected files"}), 400

    all_data_dfs = []
    processed_filenames = []
    errors = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            try:
                file.save(filepath)
                logger.info(f"File {filename} saved successfully.")

                # Attempt to parse the CSV with multiple encodings
                # and handle potential empty columns or data issues
                df = None
                possible_encodings = ["utf-8", "latin1", "iso-8859-1", "cp1252"]
                
                # First, detect encoding with chardet for a more informed guess
                try:
                    with open(filepath, "rb") as f_raw:
                        raw_data = f_raw.read()
                        detected_encoding = chardet.detect(raw_data)["encoding"]
                        if detected_encoding and detected_encoding.lower() not in [enc.lower() for enc in possible_encodings]:
                            possible_encodings.insert(0, detected_encoding) # Prioritize detected encoding
                        logger.info(f"Detected encoding for {filename}: {detected_encoding}")
                except Exception as e:
                    logger.warning(f"Chardet could not detect encoding for {filename}: {e}")

                for encoding in possible_encodings:
                    try:
                        # Read CSV, skipping blank lines and trying to infer as much as possible
                        temp_df = pd.read_csv(filepath, encoding=encoding, skip_blank_lines=True)
                        # A common issue is CSVs with extra empty columns at the end
                        temp_df.dropna(axis=1, how="all", inplace=True)
                        if not temp_df.empty:
                            df = temp_df
                            logger.info(f"Successfully parsed {filename} with encoding {encoding}")
                            break 
                    except UnicodeDecodeError:
                        logger.warning(f"Failed to parse {filename} with encoding {encoding}")
                        continue
                    except pd.errors.EmptyDataError:
                        logger.warning(f"File {filename} is empty or contains only headers.")
                        errors.append(f"File {filename} is empty or contains only headers.")
                        df = None
                        break
                    except Exception as e:
                        logger.error(f"Error parsing {filename} with encoding {encoding}: {e}")
                        errors.append(f"Error parsing {filename}: {str(e)}")
                        df = None
                        break
                
                if df is not None and not df.empty:
                    # Convert date columns to datetime objects if they exist
                    if "Date" in df.columns:
                        try:
                            df["Date"] = pd.to_datetime(df["Date"])
                        except Exception as e:
                            logger.warning(f"Could not convert 'Date' column to datetime for {filename}: {e}")
                            # errors.append(f"Warning: Could not convert 'Date' column for {filename}.")
                    
                    all_data_dfs.append(df)
                    processed_filenames.append(filename)
                    logger.info(f"Added data from {filename} for processing.")
                elif df is None and not any(f"Error parsing {filename}" in err for err in errors) and not any(f"{filename} is empty" in err for err in errors):
                     errors.append(f"Could not parse {filename} with any attempted encoding or it was empty after parsing.")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
                errors.append(f"Error processing file {filename}: {str(e)}")
            finally:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        logger.info(f"Removed temporary file {filepath}")
                    except Exception as e:
                        logger.error(f"Error removing temporary file {filepath}: {e}")
        elif file:
            errors.append(f"File type not allowed for {file.filename}. Only .csv files are accepted.")

    if not all_data_dfs:
        logger.warning(f"No dataframes were created. Errors: {errors}")
        return jsonify({"error": "No data could be parsed from the uploaded files.", "details": errors if errors else "Unknown parsing issue."}), 400

    # Combine all dataframes
    combined_df = pd.concat(all_data_dfs, ignore_index=True)
    logger.info(f"Combined {len(all_data_dfs)} dataframes into one with {len(combined_df.index)} rows.")

    # Process with MetricsAnalysisEngine
    try:
        analysis_engine = MetricsAnalysisEngine(combined_df.copy()) # Pass a copy to avoid modifying original
        kpi_summary = analysis_engine.get_campaign_performance_summary()
        keyword_performance_df = analysis_engine.get_keyword_performance()
        logger.info("Metrics analysis complete.")
    except Exception as e:
        logger.error(f"Error during metrics analysis: {e}", exc_info=True)
        errors.append(f"Error during metrics analysis: {str(e)}")
        return jsonify({"error": "Error during data analysis.", "details": errors}), 500

    # Generate recommendations
    try:
        recommendation_engine = RecommendationEngine(kpi_summary.copy(), keyword_performance_df.copy()) # Pass copies
        recommendations_list = recommendation_engine.generate_recommendations() # Gets list of strings
        logger.info("Recommendation generation complete.")
    except Exception as e:
        logger.error(f"Error during recommendation generation: {e}", exc_info=True)
        errors.append(f"Error during recommendation generation: {str(e)}")
        return jsonify({"error": "Error during recommendation generation.", "details": errors}), 500

    response_data = {
        "message": f"{len(combined_df.index)} rows of data processed from {len(processed_filenames)} files ({', '.join(processed_filenames)}).",
        "kpis": kpi_summary, # This will be a dictionary or list of dictionaries
        "recommendations": recommendations_list,
        "raw_data_preview": combined_df.head().to_dict(orient="records"),
        "full_data_for_frontend_filtering": combined_df.to_dict(orient="records"),
        "errors": errors if errors else None
    }

    # Convert NumPy types to native Python types before jsonify
    response_data_native = convert_numpy_types_to_native(response_data)
    
    return jsonify(response_data_native), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

