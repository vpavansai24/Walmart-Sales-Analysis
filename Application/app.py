from flask import Flask, render_template, g, request, make_response, redirect, url_for, flash
import os
import sqlite3
import pandas as pd
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.utils import secure_filename



app = Flask(__name__, static_url_path='/static', static_folder='static')

UPLOAD_FOLDER = 'static/uploads/'
 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.secret_key = "super secret string"
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, email, password):
        self.id = email
        self.password = password

users = {"admin": User("admin", "admin")}

# Authentication
@login_manager.user_loader
def user_loader(id):
    return users.get(id)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for("login_get"))

@app.route("/protected")
@login_required
def protected():
    return 'protected'

@app.get("/login")
def login_get():
    return render_template('login.html')

@app.post("/login")
def login_post():
    username = request.form["username"]
    password = request.form["password"]
    print(username, password)

    user = users.get(username)

    if user is None or user.password != password:
        flash('Incorrect username or password')
        return redirect(url_for("login_get"))

    login_user(user)
    return redirect(url_for('index'))

@app.get("/logout")
@login_required
def logout():
    logout_user()
    return 'Logged out successfully'
# Flask routes

@app.route("/", methods=['GET'])
@login_required
def index():
    sort_by = request.args.get('sort_by', 'StoreNumber')
    c = get_db().cursor()
    c.execute('SELECT * FROM store_details ORDER BY {}'.format(sort_by))
    results = c.fetchall()
    columns = [x[0] for x in c.description]
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    return render_template('index.html', store_details=store_details, params=request.args)

@app.route("/sales", methods=['GET'])
@login_required
def sales():
    sort_by = request.args.get('sort_by', 'StoreNumber')
    c = get_db().cursor()
    c.execute('SELECT * FROM store_details ORDER BY {}'.format(sort_by))
    results = c.fetchall()
    columns = [x[0] for x in c.description]
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    return render_template('index.html', store_details=store_details, params=request.args)


@app.route('/plot', methods=['GET', 'POST'])
@login_required
def plot():
    filename = "AM3.png"

    if request.method == 'POST':
        image_count = int(request.form.get('imageCount', 0))

        if image_count == 1:
            filename = 'AM1.png'
        elif image_count == 2:
            filename = 'AM2.png'

    return render_template('plots.html', filename=filename)


@app.route('/plot2', methods=['GET', 'POST'])
@login_required
def plot2():
    filename = "AM3.png"

    if request.method == 'POST':
        image_count = int(request.form.get('imageCount2', 0))

        if image_count == 1:
            filename = 'AM1.png'
        elif image_count == 2:
            filename = 'AM2.png'

    return render_template('plots.html', filename2=filename)


# @app.route('/plot', methods=['GET', 'POST'])
# @login_required
# def plot():
#     filename = "AM3.png"

#     if request.method == 'POST':
#         image_count = int(request.form.get('imageCount', 0))

#         if image_count == 1:
#             filename = 'AM1.png'
#         elif image_count == 2:
#             filename = 'AM2.png'

#     return render_template('plots.html', filename=filename)

# @app.route('/plot', methods=['GET', 'POST'])
# @login_required
# def plot2():
#     filename = "AM3.png"

#     if request.method == 'POST':
#         image_count = int(request.form.get('imageCount2', 0))

#         if image_count == 1:
#             filename = 'AM1.png'
#         elif image_count == 2:
#             filename = 'AM2.png'

#     return render_template('plots.html', filename=filename)
 
# @app.route('/plots', methods=['POST'])
# def upload_image():
#     if 'file' not in request.files:
#         flash('No file part')
#         return redirect(request.url)
#     file = request.files['file']
#     if file.filename == '':
#         flash('No image selected for uploading')
#         return redirect(request.url)
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         #print('upload_image filename: ' + filename)
#         flash('Image successfully uploaded and displayed below')
#         return render_template('plots.html', filename=filename)
#     else:
#         flash('Allowed image types are - png, jpg, jpeg, gif')
#         return redirect(request.url)
 
# @app.route('/display/<filename>')
# def display_image(filename):
#     #print('display_image filename: ' + filename)
#     return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route("/save", methods=['POST'])
@login_required
def save():
    data = request.json
    print(data)

    c = get_db().cursor()

    try:
        # Create the UPDATE query dynamically based on the keys and values in the dictionary
        columns_and_values = ', '.join([f"{column} = ?" for column in data.keys()])
        query = f"UPDATE store_details SET {columns_and_values} WHERE StoreNumber = ?"

        print(query, tuple(data.values()))

        values = list(data.values())
        values.append(data['StoreNumber'])

        # Execute the query with the values from the dictionary
        c.execute(query, tuple(values))

        # Commit the changes to the database
        get_db().commit()

        flash("Data updated successfully", 'success')
        # msg = "Data updated successfully."
    except sqlite3.Error as e:
        flash(f"Error: {e}", 'error')
        # msg = f"Error: {e}"

    # flash(msg)
    return redirect(url_for('index'))


@app.route('/search', methods=['GET'])
@login_required
def search():

    filter_by_column = request.args.get('filter_by', 'StoreNumber')
    filter_value = request.args.get('filter_value', '')

    # Construct the filter condition based on the column and value
    if filter_value:
        filter_condition = f"{filter_by_column} LIKE ?"
        filter_value = f"%{filter_value}%"
    else:
        filter_condition = "1"

    c = get_db().cursor()
    query = f'SELECT * FROM store_details WHERE {filter_condition}'
    c.execute(query, (filter_value,) if filter_value else ())

    results = c.fetchall()
    columns = [x[0] for x in c.description]
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    return render_template('index.html', store_details=store_details, params=request.args)

@app.route('/filter_sort', methods=['GET'])
@login_required
def filter_sort():
    sort_by = request.args.get('sort_by', 'StoreNumber')
    filter_by_column = request.args.get('filter_by', 'StoreNumber')
    filter_value = request.args.get('filter_value', '')

    print(sort_by, filter_by_column, filter_value)

    # Construct the filter condition based on the column and value
    if filter_value:
        filter_condition = f"{filter_by_column} LIKE ?"
        filter_value = f"%{filter_value}%"
    else:
        filter_condition = "1"

    c = get_db().cursor()
    query = f'SELECT * FROM store_details WHERE {filter_condition} LIMIT 2'
    c.execute(query, (filter_value,) if filter_value else ())

    # query = f'SELECT * FROM store_details WHERE {filter_condition} ORDER BY ?'
    # c.execute(query, (sort_by, filter_value) if filter_value else (sort_by,))

    # query = f'SELECT * FROM store_details WHERE {filter_condition} ORDER BY {}'.format(sort_by)
    # c.execute(query, (filter_value,) if filter_value else ())

    # c = get_db().cursor()
    # c.execute('SELECT * FROM store_details ORDER BY {}'.format(sort_by))
    results = c.fetchall()
    columns = [x[0] for x in c.description]
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    return render_template('index.html', store_details=store_details, params=request.args)


@app.route('/insert', methods=['POST'])
def insert_record():
    try:
        # Extract data from the request
        data = request.json  # Assumes data is sent as JSON

        # print(data)

        c = get_db().cursor()

        # Insert data into the store_details table
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = list(data.values())

        query = f"INSERT INTO store_details ({columns}) VALUES ({placeholders})"
        c.execute(query, values)
        get_db().commit()

        # After insertion, you may want to send a success response
        return "Insert successful", 200
    except Exception as e:
        print(f"Error during insertion: {e}")
        return "Insert failed", 500

# Route used to DELETE a specific record in the database    
@app.route("/delete", methods=['POST','GET'])
def delete():
    if request.method == 'POST':
        try:
             # Use the hidden input value of id from the form to get the storeNumber
            storeNumber = request.form['id']
            # DELETE a specific record based on storeNumber
            c = get_db().cursor()
            c.execute("DELETE FROM store_details WHERE storeNumber=?", (storeNumber))
            get_db().commit()
            msg = "Record successfully deleted from the database"
        except:
            get_db().rollback()
            msg = "Error in the DELETE"

        finally:
            # con.close()
            # Send the transaction message to result.html
            # return render_template('result.html',msg=msg)
            return redirect(url_for('index'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('./instance/database.db')
        db.set_trace_callback(print)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()