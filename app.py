from datetime import timedelta
from flask import Flask
from pages import views

app = Flask(__name__)
app.secret_key = "music1"
app.permanent_session_lifetime = timedelta(days=7)
app.register_blueprint(views, url_prefix="/")

if __name__ == '__main__':
    app.run(debug=True)