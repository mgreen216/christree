# netlify/functions/submit_message.py (Temporary Minimal Test)
import serverless_wsgi
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/submit-message', methods=['POST', 'GET']) # Allow GET for easy testing
def simple_handler():
    print("Minimal function executed!") # Log message
    return jsonify({'status': 'success', 'message': 'Minimal function says hi!'}), 200

def handler(event, context):
    print("Handler invoked") # Log message
    return serverless_wsgi.handle_request(app, event, context)
