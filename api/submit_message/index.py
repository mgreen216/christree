# /api/submit_message.py

print("Loading /api/submit_message.py module (Upstash Redis Version)...")

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
UPSTASH_REDIS_URL = os.environ.get('UPSTASH_REDIS_URL')
print(f"UPSTASH_REDIS_URL set: {'Yes' if UPSTASH_REDIS_URL else 'No'}")

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

# --- Redis Client Setup ---
# Initialize as None, connection will be attempted on first request
redis_client = None

# def get_redis_client():
#     """Initializes (if needed) and returns a Redis client connected to Upstash."""
#     global redis_client
#     # If client already exists (from a previous request in the same warm instance), reuse it
#     if redis_client:
#         print("Reusing existing Redis client instance.")
#         # Optional: Ping to ensure connection is still valid, though might add latency
#         # try:
#         #     redis_client.ping()
#         #     return redis_client
#         # except redis.exceptions.ConnectionError:
#         #     print("Existing Redis connection lost, will reconnect.")
#         #     redis_client = None # Force reconnect
#         # except Exception as ping_err:
#         #      print(f"Error pinging existing Redis connection: {ping_err}")
#         #      redis_client = None # Force reconnect
#         return redis_client # Return existing client for now

    # If no client or connection lost, try to connect
    if not UPSTASH_REDIS_URL:
        print("ERROR: UPSTASH_REDIS_URL environment variable not set.")
        raise ConnectionError("Redis URL not configured.")
    try:
        print(f"Connecting to Redis at {UPSTASH_REDIS_URL[:20]}...")
        client = redis.from_url(UPSTASH_REDIS_URL, decode_responses=True)
        client.ping() # Test connection
        print("Redis connection successful (ping successful).")
        redis_client = client # Store globally for potential reuse
        return client
    except redis.exceptions.ConnectionError as conn_err:
         print(f"ERROR connecting to Redis: {conn_err}")
         raise # Re-raise to indicate failure
    except Exception as e:
        print(f"ERROR initializing Redis client: {e}")
        raise

# --- REMOVED: Initial service connection attempt on load ---
# print("Skipping initial Redis client initialization on module load.")
# try:
#     # We don't call get_redis_client() here anymore
#     pass
# except Exception as startup_e:
#     print(f"This block is now skipped: {startup_e}")


# --- API Endpoint Definition ---
print("Defining Flask route / ...")
@app.route('/', methods=['POST'])
def submit_message_route():
    """ Flask route handler to receive messages and save to Upstash Redis """
    print("\n--- Request received (Redis Version - Connect On Request) ---")

    # Get Redis client instance - connection attempt happens here if needed
    print("Getting Redis client instance for request...")
    return jsonify({'status': 'success', 'message': 'Simplified test OK!'}), 200
    # try:
    #     r = get_redis_client()
    #     # Check again after attempting connection
    #     if not r:
    #          print("ERROR: Failed to get Redis client during request.")
    #          return jsonify({'status': 'error', 'message': 'Server configuration error (Redis connection).'}), 500
    # except Exception as req_conn_e:
    #      # Catch errors from get_redis_client() if it fails here
    #      print(f"ERROR getting Redis client during request: {req_conn_e}")
    #      return jsonify({'status': 'error', 'message': 'Server configuration error (Redis connection).'}), 500
    # print("Redis client obtained.")

    # --- The rest of the route logic remains the same ---
    # Check SPREADSHEET_ID (Should be removed if only using Redis)
    # *** Correction: Remove SPREADSHEET_ID / SHEET_RANGE_NAME checks if only using Redis ***
    # if not SPREADSHEET_ID: # REMOVE THIS CHECK
    #     print("Error: SPREADSHEET_ID environment variable not set.") # REMOVE
    #     return jsonify({'status': 'error', 'message': 'Server configuration error (Spreadsheet ID).'}), 500 # REMOVE
    # print(f"Using SPREADSHEET_ID: {SPREADSHEET_ID}") # REMOVE
    # print(f"Using SHEET_RANGE_NAME: {SHEET_RANGE_NAME}") # REMOVE

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
        # try:
        #     list_length = r.lpush(redis_list_key, message_data)
        #     print(f"LPUSH successful. List '{redis_list_key}' new length: {list_length}")

        # except redis.exceptions.RedisError as redis_err:
        #      print(f"ERROR during Redis command: {redis_err}")
        #      return jsonify({'status': 'error', 'message': 'Failed to save message to Redis store.'}), 500
        # except Exception as redis_other_err:
        #      print(f"ERROR saving to Redis (non-API error): {redis_other_err}")
        #      return jsonify({'status': 'error', 'message': 'Failed to save message to Redis store.'}), 500

        print(f"Successfully saved message to Redis: {message_text}")
        return jsonify({'status': 'success', 'message': 'Message received and saved successfully.'}), 200

    except Exception as e:
        print(f"ERROR processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'An internal server error occurred.'}), 500

print("Finished loading /api/submit_message.py module (Redis Version - Connect On Request).")
