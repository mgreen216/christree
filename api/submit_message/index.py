    # /api/submit_message/index.py (Minimal Test)

    print("Loading MINIMAL /api/submit_message/index.py module...")

    try:
        from flask import Flask, jsonify
        print("Minimal imports successful.")
    except ImportError as import_err:
        print(f"MINIMAL - FATAL IMPORT ERROR: {import_err}")
        raise

    print("Initializing minimal Flask app...")
    app = Flask(__name__)
    print("Minimal Flask app initialized.")

    # No CORS needed for this simple test if called from same origin via relative path
    # No Redis/Google setup needed

    print("Defining minimal Flask route / ...")
    @app.route('/', methods=['POST', 'GET']) # Allow GET for easy browser testing too
    def minimal_route():
        """ Minimal Flask route handler """
        print("\n--- Minimal request received ---")
        # Just return a success message immediately
        return jsonify({'status': 'success', 'message': 'Minimal Vercel function executed OK!'}), 200

    print("Finished loading MINIMAL module.")

    # Vercel's runtime should automatically pick up the 'app' object.
    
