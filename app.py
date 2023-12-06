from flask import Flask, render_template, g, request, make_response, redirect, url_for, flash
import os
import sqlite3
import pandas as pd
import plotly.express as px
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.utils import secure_filename



app = Flask(__name__)

UPLOAD_FOLDER = 'static/plots/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.secret_key = "super secret string"
login_manager = LoginManager()
login_manager.init_app(app)

# class User(UserMixin):
#     def __init__(self, email, password):
#         self.id = email
#         self.password = password

# users = {"admin": User("admin", "admin")}

class User(UserMixin):
    def __init__(self, username, password, firstname, lastname, email):
        self.id = username
        self.username = username
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.email = email

# Example user dictionary
users = {
    "admin": User("admin", "adtproject", "Admin", "User", "admin@gmail.com")
}

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


# Function to add a new user to the users dictionary
def add_user(username, password, firstname, lastname, email):
    # Check if the username is already taken
    if username in users:
        flash("Username already taken. Please choose a different username.", "success")
        return False

    # Create a new User instance and add it to the users dictionary
    new_user = User(username, password, firstname, lastname, email)
    users[username] = new_user
    users[email] = new_user
    flash("Account created successfully. You can now log in.", "success")
    return True

# Flask route for handling the signup form submission
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']

        # Call the add_user function to add the new user
        if add_user(username, password, firstname, lastname, email):
            # If user added successfully, redirect to login page or any other page
            return redirect(url_for('login_get'))

    return render_template('signup.html')

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
    c.execute('SELECT * FROM combined_sales_data ORDER BY {} LIMIT 500'.format(sort_by))
    results = c.fetchall()
    columns = [x[0] for x in c.description]
    # print("sales function columns:", columns)
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    return render_template('index_sales.html', store_details=store_details, params=request.args)


@app.route('/plot_sales', methods=['GET', 'POST'])
@login_required
def plot_store_sales():
    df = pd.read_csv('combined_sales_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])

    if request.method == 'POST':
        # Extract form data
        store_number = int(request.form['storeNumber'])
        start_date = request.form['startDate']
        end_date = request.form['endDate']

        df_filtered = df[(df['Store'] == store_number) & (df['Date'] >= start_date) & (df['Date'] <= end_date)]

        # Create line plot using Plotly Express for the filtered DataFrame
        fig = px.line(df_filtered, x='Date', y='Weekly_Sales', title=f'Weekly Sales Over Time - Store {store_number}')
        fig.update_xaxes(title_text='Date')
        fig.update_yaxes(title_text='Weekly Sales')

        # Show the plot
        fig.show()

        return render_template('plots.html')

@app.route('/plot_all_sales', methods=['GET', 'POST'])
@login_required
def plot_all_sales():
    df = pd.read_csv('combined_sales_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])

    if request.method == 'POST':
        # Extract form data
        start_date = request.form['startDate']
        end_date = request.form['endDate']

        df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

        # Create line plot using Plotly Express for all store sales
        fig = px.line(df_filtered, x='Date', y='Weekly_Sales', color='Store',
                      title=f'Weekly Sales Over Time - All Stores',
                      labels={'Weekly_Sales': 'Weekly Sales', 'Date': 'Date', 'Store': 'Store Number'})

        # fig = px.line(df_filtered, x='Date', y='Weekly_Sales', title=f'Weekly Sales Over Time - Store {store_number}')
        # fig.update_xaxes(title_text='Date')
        # fig.update_yaxes(title_text='Weekly Sales')

        # Show the plot
        fig.show()

        return render_template('plots.html')


@app.route('/plot_total_sales', methods=['GET', 'POST'])
@login_required
def plot_total_sales():
    df = pd.read_csv('combined_sales_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])

    if request.method == 'POST':
        # Extract form data
        start_date = request.form['startDate']
        end_date = request.form['endDate']

        df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

        aggregated_df = df_filtered.groupby(['Store'], as_index=False)['Weekly_Sales'].sum()

        # Sort the aggregated DataFrame by 'Weekly_Sales'
        aggregated_df = aggregated_df.sort_values(by='Weekly_Sales', ascending=False)

        # Create a bar plot using Plotly Express
        fig = px.bar(aggregated_df, x='Store', y='Weekly_Sales', title=f'Total Weekly Sales by Store from {start_date} to {end_date}',
                    labels={'Weekly_Sales': 'Total Weekly Sales', 'Store': 'Store Number'})

        # Show the plot
        fig.show()

        return render_template('plots.html')


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


# @app.route('/plot2', methods=['GET', 'POST'])
# @login_required
# def plot2():
#     filename = "AM3.png"

#     if request.method == 'POST':
#         image_count = int(request.form.get('imageCount2', 0))

#         if image_count == 1:
#             filename = 'AM1.png'
#         elif image_count == 2:
#             filename = 'AM2.png'

#     return render_template('plots.html', filename2=filename)

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

@app.route("/save_sales", methods=['POST'])
@login_required
def save_sales():
    data = request.json
    print(data)

    c = get_db().cursor()

    try:

        # Separate data into sales and conditions
        sales_data = {k: data[k] for k in ('StoreNumber', 'SalesDate', 'Weekly_Sales')}
        conditions_data = {k: data[k] for k in ('StoreNumber', 'SalesDate', 'Temperature', 'Fuel_Price', 'MarkDown1', 'MarkDown2', 
                                                'MarkDown3', 'MarkDown4', 'MarkDown5', 'CPI', 'Unemployment', 'IsHoliday')}
        
        sales_data['Date'] = sales_data.pop('SalesDate')
        conditions_data['Date'] = conditions_data.pop('SalesDate')

        sales_data['Store'] = int(sales_data.pop('StoreNumber'))
        conditions_data['Store'] = int(conditions_data.pop('StoreNumber'))

        # print(sales_data)
        # print(conditions_data)

        # Update data in the store_sales table
        sales_update_columns = ', '.join(f"{key} = ?" for key in sales_data.keys())
        sales_update_values = list(sales_data.values())

        sales_update_query = f"UPDATE store_sales SET {sales_update_columns} WHERE Store = ? AND Date = ?"
        
        # Update data in the store_conditions table
        conditions_update_columns = ', '.join(f"{key} = ?" for key in conditions_data.keys())
        conditions_update_values = list(conditions_data.values())

        conditions_update_query = f"UPDATE store_conditions SET {conditions_update_columns} WHERE Store = ? AND Date = ?"

        # Use the database connection from your get_db() function
        conn = get_db()
        cursor = conn.cursor()

        # Update store_sales
        cursor.execute(sales_update_query, sales_update_values + [sales_data['Store'], sales_data['Date']])
        # Update store_conditions
        cursor.execute(conditions_update_query, conditions_update_values + [conditions_data['Store'], conditions_data['Date']])

        conn.commit()

        flash("Data updated successfully")
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

    # Check if there are no records
    if not results:
        return render_template('no_results.html', params=request.args)
    
    columns = [x[0] for x in c.description]
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    
    return render_template('index.html', store_details=store_details, params=request.args)

@app.route('/search_sales', methods=['GET'])
@login_required
def search_sales():

    filter_by_column = request.args.get('filter_by', 'StoreNumber')
    filter_value = request.args.get('filter_value', '')

    # Construct the filter condition based on the column and value
    if filter_value:
        filter_condition = f"{filter_by_column} LIKE ?"
        filter_value = f"%{filter_value}%"
    else:
        filter_condition = "1"

    c = get_db().cursor()
    query = f'SELECT * FROM combined_sales_data WHERE {filter_condition} LIMIT 500'
    c.execute(query, (filter_value,) if filter_value else ())

    results = c.fetchall()

    # Check if there are no records
    if not results:
        return render_template('no_results.html', params=request.args)
    
    columns = [x[0] for x in c.description]
    df = pd.DataFrame(results, columns=columns)
    store_details = df.to_dict(orient='records')
    return render_template('index_sales.html', store_details=store_details, params=request.args)

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
        # flash("Inserted the record successfully")
        return "Insert successful", 200
    except Exception as e:
        flash(f"Error during insertion: {e}")
        return "Insert failed", 200


@app.route('/insert_sales', methods=['POST'])
def insert_record_sales():
    try:
        # Extract data from the request
        data = request.json  # Assumes data is sent as JSON

        # print(data)

        # Separate data into sales and conditions
        sales_data = {k: data[k] for k in ('StoreNumber', 'SalesDate', 'Weekly_Sales')}
        conditions_data = {k: data[k] for k in ('StoreNumber', 'SalesDate', 'Temperature', 'Fuel_Price', 'MarkDown1', 'MarkDown2', 
                                                'MarkDown3', 'MarkDown4', 'MarkDown5', 'CPI', 'Unemployment', 'IsHoliday')}
        
        sales_data['Date'] = sales_data.pop('SalesDate')
        conditions_data['Date'] = conditions_data.pop('SalesDate')

        sales_data['Store'] = int(sales_data.pop('StoreNumber'))
        conditions_data['Store'] = int(conditions_data.pop('StoreNumber'))

        # print(sales_data)
        # print(conditions_data)

        # Insert data into the store_sales table
        sales_columns = ', '.join(sales_data.keys())
        sales_placeholders = ', '.join(['?' for _ in sales_data])
        sales_values = list(sales_data.values())

        sales_query = f"INSERT INTO store_sales ({sales_columns}) VALUES ({sales_placeholders})"
        
        # Insert data into the store_conditions table
        conditions_columns = ', '.join(conditions_data.keys())
        conditions_placeholders = ', '.join(['?' for _ in conditions_data])
        conditions_values = list(conditions_data.values())

        conditions_query = f"INSERT INTO store_conditions ({conditions_columns}) VALUES ({conditions_placeholders})"

        # Use the database connection from your get_db() function
        conn = get_db()
        cursor = conn.cursor()

        # Insert into store_sales
        cursor.execute(sales_query, sales_values)
        # Insert into store_conditions
        cursor.execute(conditions_query, conditions_values)

        conn.commit()

        # After insertion, you may want to send a success response
        flash("Inserted the record successfully")
        return "Insert successful", 200
    except Exception as e:
        flash(f"Error during insertion: {e}")
        return "Insert failed", 200

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
            # flash("Record successfully deleted from the database")
        except:
            get_db().rollback()
            msg = "Error in the DELETE"

        finally:
            # con.close()
            # Send the transaction message to result.html
            # return render_template('result.html',msg=msg)
            return redirect(url_for('index'))

# Route used to DELETE a specific record in the database    
@app.route("/delete_sales", methods=['POST','GET'])
def delete_sales():
    if request.method == 'POST':
        try:
             # Use the hidden input value of id from the form to get the storeNumber
            storeNumber = request.form['store_number']
            salesDate = request.form['sales_date']
            
            # DELETE a specific record based on storeNumber
            c = get_db().cursor()
            c.execute("DELETE FROM store_sales WHERE Store=? AND DATE=?", (storeNumber, salesDate))
            c.execute("DELETE FROM store_conditions WHERE Store=? AND DATE=?", (storeNumber, salesDate))
            get_db().commit()
            flash("Record successfully deleted from the database")
        except:
            get_db().rollback()
            msg = "Error in the DELETE"

        finally:
            # con.close()
            # Send the transaction message to result.html
            # return render_template('result.html',msg=msg)
            return redirect(url_for('sales'))

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