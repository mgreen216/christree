# /api/submit_message/index.py (Minimal Test)

# Ensure this line and all top-level lines have NO leading spaces/tabs
print("Loading MINIMAL /api/submit_message/index.py module...")

try:
    # Ensure imports also have NO leading spaces/tabs
    from flask import Flask, jsonify
    print("Minimal imports successful.")
except ImportError as import_err:
    # Ensure this block is indented correctly (e.g., 4 spaces)
    print(f"MINIMAL - FATAL IMPORT ERROR: {import_err}")
    raise

# Ensure this line has NO leading spaces/tabs
print("Initializing minimal Flask app...")
# Ensure this line has NO leading spaces/tabs
app = Flask(__name__)
# Ensure this line has NO leading spaces/tabs
print("Minimal Flask app initialized.")

# No CORS needed for this simple test if called from same origin via relative path
# No Redis/Google setup needed

# Ensure this line has NO leading spaces/tabs
print("Defining minimal Flask route / ...")
# Ensure decorator has NO leading spaces/tabs
@app.route('/', methods=['POST', 'GET']) # Allow GET for easy browser testing too
# Ensure function definition has NO leading spaces/tabs
def minimal_route():
    """ Minimal Flask route handler """
    # Ensure code inside function IS indented (e.g., 4 spaces)
    print("\n--- Minimal request received ---")
    # Just return a success message immediately
    return jsonify({'status': 'success', 'message': 'Minimal Vercel function executed OK!'}), 200

# Ensure this line has NO leading spaces/tabs
print("Finished loading MINIMAL module.")

# Vercel's runtime should automatically pick up the 'app' object.
