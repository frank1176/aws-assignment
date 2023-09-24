from flask import Flask, render_template, request,render_template, redirect, session, url_for, flash
from pymysql import connections
import os
import boto3
from werkzeug.utils import secure_filename
from config import *
import uuid
import botocore
app = Flask(__name__,static_folder='static')
app.secret_key = os.urandom(24)

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


@app.route('/AddCompany', methods=['GET', 'POST'])
def AddCompany():
    return render_template('AddCompany.html')

@app.route('/CreateUser', methods=['GET', 'POST'])
def CreateUser():
    return render_template('CreateUser.html')

@app.route('/Supervisor', methods=['GET', 'POST'])
def Supervisor():
    return render_template('Supervisor.html')



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
            elif session['user_role'] == 'Supervisor':
                print("supervisor")
                return redirect(url_for('Supervisor'))
            elif session['user_role'] == 'Student':
                print("user")
                return redirect(url_for('Home'))    
            else:
                flash('Email or password is invalid, please try again.', 'error')
                return redirect(url_for('signin'))

@app.route('/SubmitInternshipForm', methods=['GET'])
def SubmitForm():

    try:
       # Fetch data from the database (you can replace this with your own query)
        cursor = db_conn.cursor()

        # Assuming you have a table named 'supervisors' with columns 'id' and 'name'
        cursor.execute('SELECT user_id, user_name FROM user WHERE user_role = "Supervisor"')
        supervisors = cursor.fetchall()

        # Close the database connection
        cursor.close()
    except Exception as e:
        print("An error occurred while fetching supervisor data.")
        print("Error:", str(e))
        supervisors = []  # Empty list in case of an error

    return render_template('SubmitInternshipForm.html', supervisors=supervisors)


@app.route('/submitform', methods=['POST'])
def submit_form():
    if request.method == 'POST':
        # Fetching form values
        company_name = request.form['company_name']
        company_address = request.form['company_address']
        allowance = request.form['allowance']
        uploaded_files = request.files.getlist('files[]')
        supervisor_id = request.form.get('supervisor')

        # Ensure user_id is in the session
        if 'user_id' not in session:
            return "Unauthorized", 403

        user_id = session['user_id']

        s3 = get_s3_resource()

        # Create a cursor to interact with the DB
        cursor = db_conn.cursor()
        file_id = None
        files_url=[]
        for file in uploaded_files:
            # Uploading file to S3
            unique_filename = str(uuid.uuid4())[:8] + '_' + secure_filename(file.filename)
            try:
                # Put object in S3
                s3.Bucket(custombucket).put_object(Key=unique_filename, Body=file)
            except botocore.exceptions.ClientError as e:
                print(f"Unexpected error during S3 put operation: {e}")
                return "Failed to submit form", 500

            url = f"https://{custombucket}.s3.amazonaws.com/{unique_filename}"
            files_url.append(url)
            # Insert the file information into the file table
        file_insert_sql = "INSERT INTO File (file_url, file_type) VALUES (%s, %s)"
        try:
            cursor.execute(file_insert_sql, (files_url, file.content_type))
            db_conn.commit()
        except Exception as e:
            print(f"Error inserting file into database: {e}")
            return "Failed to submit form", 500

        # Store the last inserted file_id
        file_id = cursor.lastrowid

        # After processing all files, insert a single row in the submit_form table
        # Associated with the last file's file_id
        if file_id:
            form_insert_sql = """INSERT INTO submit_form 
                (company_name, company_address, allowance, file_id, user_id,status,supervisor_id) 
                VALUES (%s, %s, %s, %s, %s,%s, %s)"""
            try:
                cursor.execute(form_insert_sql, (company_name, company_address, allowance, file_id, user_id,"", supervisor_id))
                db_conn.commit()
            except Exception as e:
                print(f"Error inserting form data into database: {e}")
                return "Failed to submit form", 500

        cursor.close()

        # After updating the database, fetch the updated data
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM user WHERE user_role = 'Supervisor'")
        supervisors = cursor.fetchall()
        print("submit_form Submitted Successfully")
        cursor.close()

    return render_template('SubmitInternshipForm.html', supervisors=supervisors)

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
    
    if email_exists:
        flash('Email already exists, please use another email.', 'error')
    else:
        # Email doesn't exist, insert the new user
        insert_sql = "INSERT INTO user (user_name, user_password, user_email, user_role) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_sql, (name, password, email, role))
        db_conn.commit()
        print(role)
        flash('User successfully created.', 'success')
        
        # Check if the role is "supervisor" and insert into the supervisor table
        if role == "Supervisor":
            user_id = cursor.lastrowid  # Get the auto-incremented user ID
            print(user_id)
            insert_supervisor_sql = "INSERT INTO supervisor (user_id) VALUES (%s)"
            cursor.execute(insert_supervisor_sql, (user_id))
            db_conn.commit()

             # Retrieve the supervisor_id from the supervisor table
            cursor.execute("SELECT supervisor_id FROM supervisor WHERE user_id = %s", (user_id,))
            supervisor_id = cursor.fetchone()[0]
            
            # Update the user table with the supervisor_id
            update_user_sql = "UPDATE user SET supervisor_id = %s WHERE user_id = %s"
            cursor.execute(update_user_sql, (supervisor_id, user_id))
            db_conn.commit()

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
        cursor.execute("SELECT company_name, company_address, company_website, company_phone, contact_name, company_description, company_status, company_logo, company_id FROM company")
        companies = cursor.fetchall()
        print(companies)  # Add this line for debugging
        cursor.close()
       
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))

    return render_template('CompanyList.html', companies=companies)

@app.route('/approval', methods=['POST'])
def approval():
    if request.method == 'POST':
        company_id = request.form.get('company_id')
        action = request.form.get('action')

        try:
            cursor = db_conn.cursor()

            if action == 'approve':
                company_status = 'approved'
            elif action == 'reject':
                company_status = 'rejected'
            else:
                # Handle invalid action value here
                pass

            cursor.execute("UPDATE company SET company_status = %s WHERE company_id = %s", (company_status, company_id))
            db_conn.commit()
            cursor.close()
        except Exception as e:
            # Handle any database errors here, e.g., print the error message
            print(f"Database error: {str(e)}")
            db_conn.rollback()  # Rollback the transaction in case of an error

        return redirect(url_for('CompanyList'))
    return render_template('CompanyList.html')

@app.route('/InternshipList', methods=['GET'])
def show_internship_list():
    try:
        # Fetch data from the database (you can replace this with your own query)
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM submit_form")
        internships = cursor.fetchall()
        print(internships)  # Add this line for debugging
        cursor.close()
       
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))

    return render_template('InternshipList.html', internships=internships)

@app.route('/SupervisorInternshipList', methods=['GET'])
def supervisor_internship_list():
    try:
        # Fetch data from the database (you can replace this with your own query)
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM submit_form")
        internships = cursor.fetchall()
        print(internships)  # Add this line for debugging
        cursor.close()
       
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))

    return render_template('SupervisorInternshipList.html', internships=internships)

@app.route('/internshipapproval', methods=['POST'])
def internshipapproval():
    if request.method == 'POST':
        submit_form_id = request.form.get('submit_form_id')
        action = request.form.get('action')

        print(submit_form_id)
        print(action)
        try:
            cursor = db_conn.cursor()

            if action == 'approve':
                status = 'approved'
            elif action == 'reject':
                status = 'rejected'
            else:
                # Handle invalid action value here
                pass

            cursor.execute("UPDATE submit_form SET status = %s WHERE submit_form_id = %s", (status, submit_form_id))
            db_conn.commit()
            cursor.close()
        except Exception as e:
            # Handle any database errors here, e.g., print the error message
            print(f"Database error: {str(e)}")
            db_conn.rollback()  # Rollback the transaction in case of an error

        # After updating the database, fetch the updated data
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM submit_form")
        internships = cursor.fetchall()
        cursor.close()

        # Pass the updated data to the template
        return render_template('InternshipList.html', internships=internships)

@app.route('/CompanyListView', methods=['GET', 'POST'])
def CompanyListView():
    try:
        # Fetch data from the database
        cursor = db_conn.cursor()
        cursor.execute("SELECT company_name, company_address, company_website, company_phone, contact_name, company_description, company_logo, company_id FROM company WHERE company_status = 'approved'")
        companies = cursor.fetchall()
        cursor.close()
       
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))
        companies = []  # Set companies to an empty list in case of an error

    return render_template('CompanyListView.html', companies=companies)

@app.route('/viewstatus', methods=['GET', 'POST'])
def viewstatus():
    # Ensure user_id is available in the session
    if 'user_id' not in session:
        # Redirect to login page (assuming it's named 'login')
        return redirect(url_for('SignIn'))

    user_id = session['user_id']

    try:
        # Fetch data from the database
        cursor = db_conn.cursor()
        # Using parameterized query for safety against SQL injection
        cursor.execute("SELECT * FROM submit_form WHERE user_id = %s", (user_id,))
        companies = cursor.fetchall()
        cursor.close()

    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))
        companies = []  # Set companies to an empty list in case of an error
        # Optionally, you can add a user-friendly error message
        flash("There was an issue retrieving your data. Please try again later.", "error")

    return render_template('status.html', companies=companies)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
