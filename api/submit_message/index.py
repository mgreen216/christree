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
    # Check if 'redis' is in requirements.txt
    raise

# --- Configuration ---
print("Reading environment variables for Upstash Redis...")
# Vercel automatically injects these when the Upstash integration is added
# Ensure the integration is added and linked to this project.
UPSTASH_REDIS_URL = os.environ.get('UPSTASH_REDIS_URL') # Or specific URL var provided by Upstash integration

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
redis_client = None

def get_redis_client():
    """Initializes and returns a Redis client connected to Upstash."""
    global redis_client
    if redis_client:
        print("Reusing existing Redis client instance.")
        return redis_client
    if not UPSTASH_REDIS_URL:
        print("ERROR: UPSTASH_REDIS_URL environment variable not set.")
        raise ConnectionError("Redis URL not configured.")
    try:
        print(f"Connecting to Redis at {UPSTASH_REDIS_URL[:20]}...") # Avoid logging full URL/password
        # decode_responses=True makes redis-py return strings instead of bytes
        client = redis.from_url(UPSTASH_REDIS_URL, decode_responses=True)
        # Test connection
        client.ping()
        print("Redis connection successful (ping successful).")
        redis_client = client
        return client
    except redis.exceptions.ConnectionError as conn_err:
         print(f"ERROR connecting to Redis: {conn_err}")
         raise # Re-raise to indicate failure
    except Exception as e:
        print(f"ERROR initializing Redis client: {e}")
        raise

# Initialize client on load
print("Attempting initial Redis client initialization...")
try:
    get_redis_client()
    print("Initial Redis client initialization successful.")
except Exception as startup_e:
    print(f"WARNING: Could not initialize Redis client on startup: {startup_e}")
    # Allow app start, endpoint will try to connect again


# --- API Endpoint Definition ---
print("Defining Flask route / ...")
@app.route('/', methods=['POST'])
def submit_message_route():
    """ Flask route handler to receive messages and save to Upstash Redis """
    print("\n--- Request received (Redis Version) ---")

    # Get Redis client instance
    print("Getting Redis client instance for request...")
    try:
        r = get_redis_client()
        if not r:
             # This might happen if initial load failed and couldn't recover
             print("ERROR: Redis client still not available for request.")
             return jsonify({'status': 'error', 'message': 'Server configuration error (Redis connection).'}), 500
    except Exception as req_conn_e:
         print(f"ERROR getting Redis client during request: {req_conn_e}")
         return jsonify({'status': 'error', 'message': 'Server configuration error (Redis connection).'}), 500
    print("Redis client obtained.")

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

        # --- Prepare data for Redis ---
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Store timestamp and message together as a JSON string in a Redis list
        message_data = json.dumps({
            "timestamp": timestamp,
            "text": message_text
        })
        redis_list_key = "submitted_messages" # Name of the list in Redis

        # --- Action: Save to Upstash Redis using LPUSH ---
        # LPUSH adds the element to the beginning of the list
        print(f"Attempting to LPUSH to Redis list: {redis_list_key}")
        try:
            list_length = r.lpush(redis_list_key, message_data)
            print(f"LPUSH successful. List '{redis_list_key}' new length: {list_length}")

            # Optional: Trim the list if it gets too long (e.g., keep last 1000)
            # r.ltrim(redis_list_key, 0, 999)

        except redis.exceptions.RedisError as redis_err:
             print(f"ERROR during Redis command: {redis_err}")
             # Attempt to reconnect or handle specific errors if needed
             # For now, return a generic server error
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

print("Finished loading /api/submit_message.py module (Redis Version).")
# Vercel's runtime should automatically pick up the 'app' object.
