# /api/submit_message.py

# Removed serverless_wsgi import
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
# Read environment variables set in Vercel Project Settings
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
SHEET_RANGE_NAME = os.environ.get('SHEET_RANGE_NAME', 'Sheet1!A:B')
# GOOGLE_APPLICATION_CREDENTIALS should contain the *content* of your service account JSON key
# It's recommended to paste the JSON content directly into the Vercel environment variable setting.

# --- Initialize Flask App ---
# Vercel expects the Flask app object, often named 'app'
app = Flask(__name__)

# --- Enable CORS ---
# Use Vercel's system environment variables for URLs
# Reference: https://vercel.com/docs/projects/environment-variables/system-environment-variables
VERCEL_URL = os.environ.get("VERCEL_URL") # Default production URL (e.g., your-site.vercel.app)
VERCEL_BRANCH_URL = os.environ.get("VERCEL_BRANCH_URL") # Preview deployment URL

# Construct allowed origins list dynamically
ALLOWED_ORIGINS = [f"https://{VERCEL_URL}" if VERCEL_URL else "*"] # Add production URL if exists
if VERCEL_BRANCH_URL and f"https://{VERCEL_BRANCH_URL}" not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(f"https://{VERCEL_BRANCH_URL}") # Add preview URL if exists and different
ALLOWED_ORIGINS.append("http://localhost:*") # Allow local development origins

print(f"Configuring CORS for origins: {ALLOWED_ORIGINS}")
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

# --- Google Sheets API Setup ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
sheets_service = None # Initialize globally

def get_sheets_service():
    """Authenticates and returns a Google Sheets service object."""
    global sheets_service
    if sheets_service:
        return sheets_service
    try:
        # Vercel needs the credentials content, usually set via GOOGLE_APPLICATION_CREDENTIALS env var
        # Ensure the env var contains the JSON content, not just a path.
        # google-auth library can handle credentials passed directly or via the env var.
        creds, _ = google.auth.default(scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        print("Google Sheets service authenticated successfully.")
        sheets_service = service
        return service
    except Exception as e:
        print(f"Error authenticating/building Google Sheets service: {e}")
        raise

# Initialize service on load to catch errors early
try:
    get_sheets_service()
except Exception as startup_e:
    print(f"WARNING: Could not initialize Google Sheets service on startup: {startup_e}")
    # Allow app to start, but endpoint will fail if service is needed


# --- API Endpoint Definition (within Flask app) ---
# Vercel maps requests to /api/submit_message to this file.
# Flask handles routing within the file. Keeping '/api/submit-message'
# as the Flask route is fine, but not strictly necessary if it's the only route.
@app.route('/', methods=['POST'])
def submit_message_route():
    """
    Flask route handler to receive messages and save to Google Sheets.
    """
    service = get_sheets_service() # Get potentially cached service
    if not service:
         return jsonify({'status': 'error', 'message': 'Server configuration error (Sheets API not initialized).'}), 500

    if not SPREADSHEET_ID:
        print("Error: SPREADSHEET_ID environment variable not set.")
        return jsonify({'status': 'error', 'message': 'Server configuration error (Spreadsheet ID).'}), 500

    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid data: "message" key missing.'}), 400
        message_text = data['message']
        if not isinstance(message_text, str) or not message_text.strip():
             return jsonify({'status': 'error', 'message': 'Invalid data: Message cannot be empty.'}), 400

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        values_to_append = [[timestamp, message_text]]
        body = {'values': values_to_append}

        print(f"Attempting to append to Sheet ID: {SPREADSHEET_ID}, Range: {SHEET_RANGE_NAME}")
        try:
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID, range=SHEET_RANGE_NAME,
                valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            print(f"Append result: {result.get('updates').get('updatedCells')} cells updated.")
        except HttpError as error:
            print(f"An API error occurred: {error}")
            error_details = error.resp.get('content', '{}')
            print(f"Error details: {error_details}")
            return jsonify({'status': 'error', 'message': f'Google Sheets API Error: Status {error.resp.status}'}), 500
        except Exception as sheet_error:
             print(f"Error appending to Google Sheet: {sheet_error}")
             return jsonify({'status': 'error', 'message': 'Failed to save message to sheet.'}), 500

        print(f"Successfully appended message to Google Sheet: {message_text}")
        return jsonify({'status': 'success', 'message': 'Message received and saved successfully.'}), 200

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500

# --- NO handler function needed ---
# --- NO app.run() needed ---
# Vercel detects the 'app = Flask(__name__)' object and handles running it.
