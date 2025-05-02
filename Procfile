web: gunicorn app:app
```
* `web:` declares a web dyno (process).
* `gunicorn` is the WSGI server.
* `app:app` tells Gunicorn to look for a variable named `app` (your Flask instance) inside a file named `app.py`.

**4. `runtime.txt` (Optional but Recommended)**

Create a file named `runtime.txt` in your project root to specify the Python version Heroku should use. Check Heroku's documentation for currently supported versions (e.g., 3.11.x, 3.10.x).


```text
python-3.11.9
```
*(Replace with a supported version listed in Heroku doc
