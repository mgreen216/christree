# /api/submit_message.py

print("Loading /api/submit_message.py module (Vercel KV Version)...")

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import datetime
    import os
    import requests # To interact with Vercel KV REST API
    import json     # To format data for KV
    import uuid     # To generate unique keys for messages
    print("Imports successful.")
except ImportError as import_err:
    print(f"FATAL IMPORT ERROR: {import_err}")
    raise

# --- Configuration ---
print("Reading environment variables for Vercel KV...")
# These are automatically provided by Vercel when a KV store is linked
KV_REST_API_URL = os.environ.get('KV_REST_API_URL')
KV_REST_API_TOKEN = os.environ.get('KV_REST_API_TOKEN')
# KV_REST_API_READ_ONLY_TOKEN = os.environ.get('KV_REST_API_READ_ONLY_TOKEN') # Not needed for writing

print(f"KV_REST_API_URL set: {'Yes' if KV_REST_API_URL else 'No'}")
print(f"KV_REST_API_TOKEN set: {'Yes' if KV_REST_API_TOKEN else 'No'}")

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

# --- No Google Sheets Setup Needed ---

# --- API Endpoint Definition ---
print("Defining Flask route / ...")
@app.route('/', methods=['POST'])
def submit_message_route():
    """ Flask route handler to receive messages and save to Vercel KV """
    print("\n--- Request received (KV Version) ---")

    # Check if KV environment variables are present
    if not KV_REST_API_URL or not KV_REST_API_TOKEN:
        print("ERROR: Vercel KV environment variables not configured.")
        return jsonify({'status': 'error', 'message': 'Server configuration error (KV Store).'}), 500

    try:
        print("Attempting to get JSON data from request...")
        data = request.get_json()
        print(f"Received data: {data}")

        if not data or 'message' not in data:
            print("ERROR: Invalid data, 'message' key missing.")
            return jsonify({'status': 'error', 'message': 'Invalid data: "message" key missing.'}), 400
        message_text = data['message']
        if not isinstance(message_text, str) or not message_text.strip():
             print("ERROR: Invalid data, message empty or not string.")
             return jsonify({'status': 'error', 'message': 'Invalid data: Message cannot be empty.'}), 400
        print(f"Validated message: {message_text}")

        # --- Prepare data for Vercel KV ---
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Create a unique key for each message, e.g., using timestamp and a UUID
        message_key = f"message:{timestamp}:{uuid.uuid4()}"
        # Store timestamp and message together as a JSON string value
        message_value = json.dumps({
            "timestamp": timestamp,
            "text": message_text
        })

        # --- Action: Save to Vercel KV using REST API SET command ---
        # Ref: https://vercel.com/docs/storage/vercel-kv/rest-api#set
        kv_set_url = f"{KV_REST_API_URL}/set/{message_key}"
        headers = {
            'Authorization': f'Bearer {KV_REST_API_TOKEN}'
        }

        print(f"Attempting to save to Vercel KV: Key={message_key}")
        try:
            response = requests.post(kv_set_url, headers=headers, data=message_value)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            response_json = response.json()
            print(f"Vercel KV SET Response: {response_json}")
            if response_json.get("result") != "OK":
                 print(f"ERROR: Vercel KV SET command did not return OK. Response: {response_json}")
                 return jsonify({'status': 'error', 'message': 'Failed to save message to KV store (non-OK response).'}), 500

        except requests.exceptions.RequestException as req_error:
             print(f"ERROR during Vercel KV API call: {req_error}")
             # Attempt to get more details from response if available
             error_details = "N/A"
             if req_error.response is not None:
                  error_details = req_error.response.text
             print(f"Error details: {error_details}")
             return jsonify({'status': 'error', 'message': f'KV Store API Error: {req_error}'}), 500
        except Exception as kv_error:
             print(f"ERROR saving to Vercel KV (non-API error): {kv_error}")
             return jsonify({'status': 'error', 'message': 'Failed to save message to KV store.'}), 500

        print(f"Successfully saved message to Vercel KV: Key={message_key}")
        return jsonify({'status': 'success', 'message': 'Message received and saved successfully.'}), 200

    except Exception as e:
        print(f"ERROR processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500

print("Finished loading /api/submit_message.py module (KV Version).")
# Vercel's runtime should automatically pick up the 'app' object.
