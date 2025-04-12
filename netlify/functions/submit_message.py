# netlify/functions/submit_message.py

# Use serverless-wsgi to wrap the Flask app
import serverless_wsgi
from flask import Flask, request, jsonify
# CORS is still needed if your frontend might call from a preview URL different from the main site URL
# or if you intend to call this from elsewhere. For simple same-site calls via relative paths,
# it might not be strictly necessary, but it's safer to include and configure properly.
from flask_cors import CORS
import datetime
import os
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
# Read environment variables set in Netlify UI
# (Site configuration > Build & deploy > Environment)
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
SHEET_RANGE_NAME = os.environ.get('SHEET_RANGE_NAME', 'Sheet1!A:B') # Default if not set
# GOOGLE_APPLICATION_CREDENTIALS should also be set as an environment variable
# containing the JSON key content or path (Netlify handles paths well).

# --- Initialize Flask App ---
# This part remains largely the same
app = Flask(__name__)

# --- Enable CORS ---
# Allow requests from your Netlify site URL(s).
# You might need to allow preview URLs too if testing deploy previews.
# Get your main site URL after deploying the frontend.
FRONTEND_URL = os.environ.get("URL", "*") # Get site's primary URL from Netlify env var, default to *
DEPLOY_PRIME_URL = os.environ.get("DEPLOY_PRIME_URL", "*") # Get deploy preview URL, default to *
ALLOWED_ORIGINS = [FRONTEND_URL, DEPLOY_PRIME_URL, "http://localhost:*"] # Allow local dev too
# More specific CORS config
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

# --- Google Sheets API Setup ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
sheets_service = None # Initialize globally

def get_sheets_service():
    """Authenticates and returns a Google Sheets service object."""
    global sheets_service # Modify global variable
    if sheets_service: # Reuse if already created in this instance
        return sheets_service
    try:
        # Credentials should be found via GOOGLE_APPLICATION_CREDENTIALS env var
        creds, _ = google.auth.default(scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        print("Google Sheets service authenticated successfully.")
        sheets_service = service # Store globally
        return service
    except Exception as e:
        print(f"Error authenticating/building Google Sheets service: {e}")
        raise # Re-raise

# --- API Endpoint Definition (within Flask app) ---
# The path here (/api/submit-message) defines the route *within* the Flask app context.
# The actual URL endpoint will be determined by the filename (submit_message.py)
# resulting in something like /.netlify/functions/submit-message
@app.route('/api/submit-message', methods=['POST'])
def submit_message_route():
    """
    Flask route handler to receive messages and save to Google Sheets.
    """
    # Attempt to get/initialize the service for this request if needed
    try:
        service = get_sheets_service()
        if not service:
             return jsonify({'status': 'error', 'message': 'Server configuration error (Sheets API not initialized).'}), 500
    except Exception as auth_e:
         print(f"Auth Error during request: {auth_e}")
         return jsonify({'status': 'error', 'message': 'Server configuration error (Sheets API Auth).'}), 500

    # Check config environment variables
    if not SPREADSHEET_ID:
        print("Error: SPREADSHEET_ID environment variable not set.")
        return jsonify({'status': 'error', 'message': 'Server configuration error (Spreadsheet ID).'}), 500

    try:
        # 1. Get JSON data
        data = request.get_json()

        # 2. Validate input
        if not data or 'message' not in data:
            return jsonify({'status': 'error', 'message': 'Invalid data: "message" key missing.'}), 400
        message_text = data['message']
        if not isinstance(message_text, str) or not message_text.strip():
             return jsonify({'status': 'error', 'message': 'Invalid data: Message cannot be empty.'}), 400

        # 3. Prepare data for Google Sheets
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        values_to_append = [[timestamp, message_text]]
        body = {'values': values_to_append}

        # --- Action: Append to Google Sheet ---
        print(f"Attempting to append to Sheet ID: {SPREADSHEET_ID}, Range: {SHEET_RANGE_NAME}")
        try:
            result = service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=SHEET_RANGE_NAME,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
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

        # 4. Return a success response
        print(f"Successfully appended message to Google Sheet: {message_text}")
        return jsonify({'status': 'success', 'message': 'Message received and saved successfully.'}), 200

    except Exception as e:
        # 5. Handle unexpected errors
        print(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500

# --- Netlify Handler Function ---
# This is the entry point Netlify calls. It uses serverless_wsgi to pass
# the request to our Flask app ('app').
def handler(event, context):
    # Make sure the service is initialized before handling requests
    # This helps manage state across potential cold starts/re-uses
    try:
       get_sheets_service()
    except Exception as init_e:
        print(f"Error ensuring Sheets service is initialized in handler: {init_e}")
        # Return an error response immediately if service can't init
        return {'statusCode': 500, 'body': '{"status":"error", "message":"Server configuration error (Sheets API init failed)."}'}

    return serverless_wsgi.handle_request(app, event, context)

# --- IMPORTANT: Remove the app.run() block ---
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)
# --- Netlify runs the 'handler' function, not app.run() ---
