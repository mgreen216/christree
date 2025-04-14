# /api/submit_message.py

print("Loading /api/submit_message.py module...") # Check if file loads

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import datetime
    import os
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    print("Imports successful.") # Check imports
except ImportError as import_err:
    print(f"FATAL IMPORT ERROR: {import_err}") # Log import errors
    # If imports fail, the app object won't be created, potentially causing 404
    raise # Re-raise to ensure Vercel sees the failure

# --- Configuration ---
print("Reading environment variables...")
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
SHEET_RANGE_NAME = os.environ.get('SHEET_RANGE_NAME', 'Sheet1!A:B')
# GOOGLE_APPLICATION_CREDENTIALS content expected in env var
print(f"SPREADSHEET_ID found: {'Yes' if SPREADSHEET_ID else 'No'}")
print(f"SHEET_RANGE_NAME: {SHEET_RANGE_NAME}")
# Avoid printing credentials content, just check presence
creds_env_var = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
print(f"GOOGLE_APPLICATION_CREDENTIALS set: {'Yes' if creds_env_var else 'No'}")


# --- Initialize Flask App ---
print("Initializing Flask app...")
app = Flask(__name__)
print("Flask app initialized.")

# --- Enable CORS ---
VERCEL_URL = os.environ.get("VERCEL_URL")
VERCEL_BRANCH_URL = os.environ.get("VERCEL_BRANCH_URL")
ALLOWED_ORIGINS = [f"https://{VERCEL_URL}" if VERCEL_URL else "*"]
if VERCEL_BRANCH_URL and f"https://{VERCEL_BRANCH_URL}" not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(f"https://{VERCEL_BRANCH_URL}")
ALLOWED_ORIGINS.append("http://localhost:*")
print(f"Configuring CORS for origins: {ALLOWED_ORIGINS}")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})
print("CORS configured.")

# --- Google Sheets API Setup ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
sheets_service = None

def get_sheets_service():
    """Authenticates and returns a Google Sheets service object."""
    global sheets_service
    if sheets_service:
        print("Reusing existing Sheets service instance.")
        return sheets_service
    try:
        print("Attempting Google Auth default...")
        creds, _ = google.auth.default(scopes=SCOPES)
        print("Google Auth successful. Building Sheets service...")
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        print("Google Sheets service built successfully.")
        sheets_service = service
        return service
    except Exception as e:
        print(f"ERROR authenticating/building Google Sheets service: {e}")
        raise # Re-raise

# Initialize service on load
print("Attempting initial Google Sheets service initialization...")
try:
    get_sheets_service()
    print("Initial Google Sheets service initialization successful.")
except Exception as startup_e:
    # Log warning but allow app object creation
    print(f"WARNING: Could not initialize Google Sheets service on startup: {startup_e}")


# --- API Endpoint Definition ---
print("Defining Flask route / ...") # Updated print for clarity
# Using '/' route as discussed, assuming Vercel handles mapping /api/submit_message to this file
@app.route('/', methods=['POST'])
def submit_message_route():
    """ Flask route handler """
    print("\n--- Request received ---") # Log request entry

    # Get service instance (might re-auth if initial failed or instance expired)
    print("Getting Sheets service instance for request...")
    service = get_sheets_service()
    if not service:
         print("ERROR: Sheets service not available for request.")
         return jsonify({'status': 'error', 'message': 'Server configuration error (Sheets API not initialized).'}), 500
    print("Sheets service obtained.")

    # Check environment variables again (in case they were missing on init)
    if not SPREADSHEET_ID:
        print("ERROR: SPREADSHEET_ID env var missing.")
        return jsonify({'status': 'error', 'message': 'Server configuration error (Spreadsheet ID).'}), 500
    print(f"Using SPREADSHEET_ID: {SPREADSHEET_ID}")
    print(f"Using SHEET_RANGE_NAME: {SHEET_RANGE_NAME}")

    try:
        print("Attempting to get JSON data from request...")
        data = request.get_json()
        print(f"Received data: {data}") # Log received data (be careful with sensitive data in real apps)

        if not data or 'message' not in data:
            print("ERROR: Invalid data, 'message' key missing.")
            return jsonify({'status': 'error', 'message': 'Invalid data: "message" key missing.'}), 400
        message_text = data['message']
        if not isinstance(message_text, str) or not message_text.strip():
             print("ERROR: Invalid data, message empty or not string.")
             return jsonify({'status': 'error', 'message': 'Invalid data: Message cannot be empty.'}), 400
        print(f"Validated message: {message_text}")

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        values_to_append = [[timestamp, message_text]]
        body = {'values': values_to_append}
        print(f"Prepared data for Sheets: {body}")

        # --- Action: Append to Google Sheet ---
        print(f"Attempting to append to Sheet...")
        try:
            # --- TEMPORARY SIMPLIFICATION (Optional): Comment out the actual API call ---
            # print(">>> Skipping actual Sheets API call for testing <<<")
            # result = {'updates': {'updatedCells': 'SKIPPED'}} # Fake result
            # --- UNCOMMENT BELOW TO RE-ENABLE ---
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE_NAME,
                valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            print(f"Append result: {result.get('updates', {}).get('updatedCells', 'N/A')} cells updated.") # Safer get

        except HttpError as error:
            print(f"ERROR during Sheets API call: {error}")
            error_details = "N/A"
            if hasattr(error, 'resp') and error.resp:
                 error_details = error.resp.get('content', '{}')
            print(f"Error details: {error_details}")
            return jsonify({'status': 'error', 'message': f'Google Sheets API Error: Status {getattr(error.resp, "status", "Unknown")}'}), 500
        except Exception as sheet_error:
             print(f"ERROR appending to Google Sheet (non-API error): {sheet_error}")
             return jsonify({'status': 'error', 'message': 'Failed to save message to sheet.'}), 500

        print(f"Successfully processed message: {message_text}")
        return jsonify({'status': 'success', 'message': 'Message received and saved successfully.'}), 200

    except Exception as e:
        print(f"ERROR processing request: {e}")
        # Log the full traceback for unexpected errors
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500

print("Finished loading /api/submit_message.py module.") # Check if file loads completely

# Vercel's runtime should automatically pick up the 'app' object.
# No handler function or app.run() needed.
