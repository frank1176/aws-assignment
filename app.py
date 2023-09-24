from flask import Flask, render_template, request,render_template, redirect, session, url_for, flash
from pymysql import connections
import os
import boto3
from werkzeug.utils import secure_filename
from config import *
import uuid
import botocore
app = Flask(__name__,static_folder='static')

# app.secret_key = 'pI9mFaoOhNaC/24tqBLbp+xbVXGAtx4wNE5W1tvw'

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
def get_s3_resource():
    return boto3.resource('s3')

@app.route('/', methods=['GET', 'POST'])
def SignIn():
    return render_template('SignIn.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    return render_template('SignIn.html')

@app.route('/Home', methods=['GET', 'POST'])
def Home():
    return render_template('Home.html')

@app.route('/About', methods=['GET', 'POST'])
def About():
    return render_template('About.html')

@app.route('/SubmitInternshipForm', methods=['GET', 'POST'])
def SubmitForm():
    return render_template('SubmitInternshipForm.html')

@app.route('/AddCompany', methods=['GET', 'POST'])
def AddCompany():
    return render_template('AddCompany.html')

@app.route('/CreateUser', methods=['GET', 'POST'])
def CreateUser():
    return render_template('CreateUser.html')

@app.route('/Admin', methods=['GET'])
def Admin():
    try:
        # Fetch data from the database (you can replace this with your own query)
        cursor = db_conn.cursor()
        cursor.execute("SELECT user_id, user_name, user_email, user_role FROM user")
        users = cursor.fetchall()
        print(users)  # Add this line for debugging
        cursor.close()
        return render_template('Admin.html', users=users)
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))

@app.route('/usersignin', methods=['POST'])
def userSignIn():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the user exists in the user table
        cursor = db_conn.cursor()
        cursor.execute("SELECT user_id, user_name, user_email, user_role FROM user WHERE user_email = %s AND user_password = %s", (email, password))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data:
            # User exists, store user data in session
            session['user_id'] = user_data[0]
            session['user_name'] = user_data[1]
            session['user_email'] = user_data[2]
            session['user_role'] = user_data[3]

            # Redirect based on user role
            if session['user_role'] == 'Admin':
                print("admin")
                return redirect(url_for('Admin'))
            else:
                print("user")
                return redirect(url_for('Home'))
        else:
            flash('Email or password is invalid, please try again.', 'error')
            return redirect(url_for('signin'))


@app.route('/submitform', methods=['POST'])
def submit_form():
    if request.method == 'POST':
        company_name = request.form['company_name']
        company_address = request.form['company_address']
        allowance = request.form['allowance']
        uploaded_files = request.files.getlist('files[]')
        
        # Ensure user_id is in the session
        if 'user_id' not in session:
            return "Unauthorized", 403

        user_id = session['user_id']

        # Store unique filenames
        unique_file_names = []

        s3 = get_s3_resource() 
        
        for file in uploaded_files:
            # TODO: Add file type & size checks here
            unique_filename = str(uuid.uuid4())[:8] + '_' + secure_filename(file.filename)
            try:
                # Put object in S3
                s3.Bucket(custombucket).put_object(Key=unique_filename, Body=file)
                unique_file_names.append(unique_filename)
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ExpiredToken':
                    # Handle the expired token: refresh the token and retry the operation
                    # For now, just print an error and break out of the loop
                    print("Token expired, please refresh the token and try again!")
                    break
                else:
                    # Handle other potential errors
                    print(f"Unexpected error during S3 put operation: {e}")
                    break

        file_names_string = ",".join(unique_file_names)
        insert_sql = "INSERT INTO submit_form (company_name, company_address, allowance, file_names, user_id) VALUES (%s, %s, %s, %s, %s)"
        
        cursor = db_conn.cursor()
        try:
            cursor.execute(insert_sql, (company_name, company_address, allowance, file_names_string, user_id))
            db_conn.commit()
        except Exception as e:
            print(f"Error inserting into database: {e}")
            return "Failed to submit form", 500
        finally:
            cursor.close()

        print("submit_form Submitted Successfully")
    
    return render_template('SubmitInternshipForm.html')

@app.route('/submituser', methods=['POST'])
def create_user():
    name = request.form['name']
    password = request.form['password']
    email = request.form['email']
    role = request.form['role']
    
    # Check if the email already exists in the database
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user WHERE user_email = %s", (email,))
    email_exists = cursor.fetchone()[0]
    cursor.close()
    
    if email_exists:
        flash('Email already exists, please use another email.', 'error')
    else:
        # Email doesn't exist, insert the new user
        insert_sql = "INSERT INTO user (user_name, user_password, user_email, user_role) VALUES (%s, %s, %s, %s)"
        cursor = db_conn.cursor()
        try:
            cursor.execute(insert_sql, (name, password, email, role))
            db_conn.commit()
            flash('User successfully created.', 'success')
        except Exception as e:
            db_conn.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
        finally:
            cursor.close()

    return render_template('CreateUser.html')


# In your AddCompany route
@app.route('/submit-company', methods=['POST'])
def company():
    try:
        if request.method == 'POST':

              # Ensure user_id is in the session
            if 'user_id' not in session:
                return "Unauthorized", 403

            user_id = session['user_id']
            company_name = request.form['company_name']
            company_address = request.form['company_address']
            company_website = request.form['company_website']
            company_phone = request.form['company_phone']
            contact_name = request.form['contact_name']
            company_description = request.form['company_description']
            company_logo = request.files.getlist('company_logo[]')

            if not company_name or not company_address:
                flash('Company Name and Address are required fields.', 'error')
                return redirect(url_for('AddCompany'))  # Redirect to the company submission form

            # Store unique URLs
            unique_file_urls = []
            s3 = boto3.resource('s3')  # Use resource method to create S3 resource

            for file in company_logo:
                if file.filename != '':
                    # Generate a unique filename
                    unique_filename = str(uuid.uuid4())[:8] + '_' + secure_filename(file.filename)

                    # Upload to S3
                    s3.Bucket(custombucket).upload_fileobj(file, unique_filename)  # Use upload_fileobj method

                    # Generate the full URL and append it to the list
                    url = f"https://{custombucket}.s3.amazonaws.com/{unique_filename}"
                    unique_file_urls.append(url)

            # Convert list of URLs to a comma-separated string
            file_urls_string = ",".join(unique_file_urls)

            # Modify the insert SQL to include the new column for file URLs
            insert_sql = "INSERT INTO company (company_name, company_address, company_website, company_phone, contact_name, company_description, company_logo, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

            cursor = db_conn.cursor()
            try:
                cursor.execute(insert_sql, (company_name, company_address, company_website, company_phone, contact_name, company_description, file_urls_string, user_id))
                print("Company information submitted successfully!")
                db_conn.commit()
                
            except Exception as e:
                db_conn.rollback()
                print("Error: Could not save company information. Please try again later.")
                print("Database Error:", str(e))
            finally:
                cursor.close()
    
        return redirect(url_for('AddCompany'))  # Redirect to the company submission form
    except Exception as e:
        print("An error occurred. Please try again later.")
        print("Error:", str(e))
       

    return render_template('AddCompany.html')  # Render the company submission form if there is a GET request


@app.route('/CompanyList', methods=['GET'])
def CompanyList():
    try:
        # Fetch data from the database (you can replace this with your own query)
        cursor = db_conn.cursor()
        cursor.execute("SELECT company_name, company_address, company_website, company_phone, contact_name, company_description, company_status, company_logo FROM company")
        companies = cursor.fetchall()
        print(companies)  # Add this line for debugging
        cursor.close()
       
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))

    return render_template('CompanyList.html', companies=companies)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
