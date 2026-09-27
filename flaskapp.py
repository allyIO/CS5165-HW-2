from flask import Flask, request, g, render_template, redirect, url_for, send_file
from io import BytesIO
import sqlite3

app = Flask(__name__)
DATABASE = '/var/www/html/flaskapp/ohao.db'

app.config.from_object(__name__)

def connect_to_database():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def execute_query(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    rows = cur.fetchall()
    cur.close()
    return rows

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/log-in')
def log_in():
    return render_template('login.html')

@app.route('/login', methods=['POST']) 
def login():
    username = request.form['username']
    password = request.form['password']

    users = execute_query("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    if len(users) > 0:
        return redirect(url_for('profile', username=username))
    else:
        return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    address = request.form['address']
    file = request.files.get("file")
    filecontent = file.read()


    execute_query("INSERT INTO users (username, password, firstname, lastname, email, address, filename, filecontent) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (username, password, firstname, lastname, email, address, file.filename, filecontent))

    return redirect(url_for('profile', username=username))

@app.route('/profile/<username>')
def profile(username):
    users = execute_query("SELECT * FROM users WHERE username=?", (username,))

    #compute word count
    filecontent = users[0]['filecontent']
    if filecontent:
        text = filecontent.decode('utf-8', errors='ignore')
        word_count = len(text.split())
    else:
        word_count = 0

    return render_template('profile.html', user=users[0], word_count=word_count)

@app.route("/download/<username>")
def download(username):
    files = execute_query("SELECT filename, filecontent FROM users WHERE username=?", (username,))

    if not files:
        return "File not found"

    return send_file(
        BytesIO(files[0]["filecontent"]),
        as_attachment=True,
        download_name=files[0]["filename"],
        mimetype="text/plain",
    )

#SQL setup
conn = sqlite3.connect(DATABASE)
cur = conn.cursor()
#cur.execute("""DROP TABLE IF EXISTS users""")
cur.execute("""CREATE TABLE IF NOT EXISTS users
            (id integer primary key autoincrement,username text, password text, firstname text, lastname text, email text, address text, filename text, filecontent blob)""")

conn.commit()
conn.close()

if __name__ == '__main__':
    app.run(debug=True)
