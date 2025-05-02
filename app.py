# app.py (for Heroku deployment)

print("Loading app.py module (Heroku - Upstash Redis Version)...")

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import datetime
    import os
    import redis # Use the official redis-py client
    import json  # To store structured data in Redis
    print("Imports successful.")
except ImportError as import_err:
    print(f"FATAL IMPORT ERROR: {import_err}")
    raise

# --- Configuration ---
print("Reading environment variables for Upstash Redis...")
# Heroku uses Config Vars (set in the Heroku dashboard)
UPSTASH_REDIS_URL = os.environ.get('UPSTASH_REDIS_URL')
# Get the PORT environment variable Heroku assigns
PORT = int(os.environ.get('PORT', 5000)) # Default to 5000 for local testing if PORT not set

print(f"UPSTASH_REDIS_URL set: {'Yes' if UPSTASH_REDIS_URL else 'No'}")
print(f"PORT set by Heroku (or default): {PORT}")

# --- Initialize Flask App ---
print("Initializing Flask app...")
app = Flask(__name__)
print("Flask app initialized.")

# --- Enable CORS ---
# Get your Vercel frontend URL after deployment
# Set this as a Config Var in Heroku, e.g., FRONTEND_URL='https://christree.vercel.app'
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*") # Default to allow all if not set
ALLOWED_ORIGINS = [FRONTEND_URL, "http://localhost:*"] # Allow Vercel URL and local dev
print(f"Configuring CORS for origins: {ALLOWED_ORIGINS}")
# Allow credentials if needed in future, origins list is important
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)
print("CORS configured.")

# --- Redis Client Setup ---
redis_client = None

def get_redis_client():
    """Initializes (if needed) and returns a Redis client connected to Upstash."""
    global redis_client
    if redis_client:
        print("Reusing existing Redis client instance.")
        # Optional: Add ping check here if needed
        return redis_client

    if not UPSTASH_REDIS_URL:
        print("ERROR: UPSTASH_REDIS_URL environment variable not set.")
        raise ConnectionError("Redis URL not configured.")
    try:
        print(f"Connecting to Redis at {UPSTASH_REDIS_URL[:20]}...")
        client = redis.from_url(UPSTASH_REDIS_URL, decode_responses=True)
        client.ping() # Test connection
        print("Redis connection successful (ping successful).")
        redis_client = client
        return client
    except redis.exceptions.ConnectionError as conn_err:
         print(f"ERROR connecting to Redis: {conn_err}")
         raise
    except Exception as e:
        print(f"ERROR initializing Redis client: {e}")
        raise

# --- API Endpoint Definition ---
# Define the route Flask will listen for
@app.route('/api/submit-message', methods=['POST'])
def submit_message_route():
    """ Flask route handler to receive messages and save to Upstash Redis """
    print("\n--- Request received at /api/submit-message (Heroku) ---")

    # Get Redis client instance
    print("Getting Redis client instance for request...")
    try:
        r = get_redis_client()
        if not r:
             print("ERROR: Failed to get Redis client during request.")
             return jsonify({'status': 'error', 'message': 'Server configuration error (Redis connection).'}), 500
    except Exception as req_conn_e:
         print(f"ERROR getting Redis client during request: {req_conn_e}")
         return jsonify({'status': 'error', 'message': 'Server configuration error (Redis connection).'}), 500
    print("Redis client obtained.")

    # --- Route logic ---
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

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        message_data = json.dumps({
            "timestamp": timestamp,
            "text": message_text
        })
        redis_list_key = "submitted_messages"

        print(f"Attempting to LPUSH to Redis list: {redis_list_key}")
        try:
            list_length = r.lpush(redis_list_key, message_data)
            print(f"LPUSH successful. List '{redis_list_key}' new length: {list_length}")

        except redis.exceptions.RedisError as redis_err:
             print(f"ERROR during Redis command: {redis_err}")
             return jsonify({'status': 'error', 'message': 'Failed to save message to Redis store.'}), 500
        except Exception as redis_other_err:
             print(f"ERROR saving to Redis (non-API error): {redis_other_err}")
             return jsonify({'status': 'error', 'message': 'Failed to save message to Redis store.'}), 500

        print(f"Successfully saved message to Redis: {message_text}")
        return jsonify({'status': 'success', 'message': 'Message received and saved successfully.'}), 200

    except Exception as e:
        print(f"ERROR processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500

# --- Run for Local Development (Optional) ---
# This block is NOT used by Heroku/Gunicorn, but useful for local testing
if __name__ == '__main__':
    print(f"Starting Flask development server on port {PORT}...")
    # Use 0.0.0.0 to be accessible on network, debug=True for development
    app.run(debug=True, host='0.0.0.0', port=PORT)

print("Finished loading app.py module.")
