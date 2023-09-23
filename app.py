from flask import Flask, render_template, request,render_template, redirect, url_for, flash
from pymysql import connections
import os
import boto3
from werkzeug.utils import secure_filename
from config import *
import uuid
app = Flask(__name__,static_folder='static')

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

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('CreateUser.html')

@app.route('/SignIn', methods=['GET', 'POST'])
def signin():
    return render_template('SignIn.html')

@app.route('/SubmitInternshipForm', methods=['GET', 'POST'])
def SubmitForm():
    return render_template('SubmitInternshipForm.html')


@app.route('/submitform', methods=['POST'])
def submit_form():
    if request.method == 'POST':
        company_name = request.form['company_name']
        company_address = request.form['company_address']
        allowance = request.form['allowance']
        uploaded_files = request.files.getlist('files[]')


         # Store unique filenames
        unique_file_names = []
        s3 = boto3.resource('s3')

        for file in uploaded_files:
            # Generate a unique filename
            unique_filename = str(uuid.uuid4())[:8]  + '_' + secure_filename(file.filename)
            
            # Upload to S3
            s3.Bucket(custombucket).put_object(Key=unique_filename, Body=file)
            
            # Appending unique filename to the list
            unique_file_names.append(unique_filename)

        # Convert list of filenames to a comma-separated string
        file_names_string = ",".join(unique_file_names)

        # Modify the insert SQL to include the new column for file names
        insert_sql = "INSERT INTO submit_form (company_name, company_address, allowance, file_names) VALUES (%s, %s, %s, %s)"
        
        cursor = db_conn.cursor()
        try:
            cursor.execute(insert_sql, (company_name, company_address, allowance, file_names_string))
            db_conn.commit()
        finally:
            cursor.close()

        print("submit_form Submmited Successfully")
    

    # Render the form page. You can also return a template if you have one.
    return render_template('SubmitInternshipForm.html')  # Replace with your template name

@app.route('/submituser', methods=['POST'])
def create_user():
    name = request.form['name']
    password = request.form['password']
    email = request.form['email']
    role = request.form['role']
    
    insert_sql = "INSERT INTO user (user_name, user_password, user_email, user_role) VALUES (%s, %s, %s, %s)"

    cursor = db_conn.cursor()
    try:
        cursor.execute(insert_sql, (name, password, email, role))
        db_conn.commit()
    finally:
        cursor.close()
    
    return render_template('CreateUser.html')


@app.route('/AddCompany', methods=['GET', 'POST'])
def AddCompany():
    return render_template('AddCompany.html')

# In your AddCompany route
@app.route('/submit-company', methods=['POST'])
def company():
    try:
        if request.method == 'POST':
            company_name = request.form['company_name']
            company_address = request.form['company_address']
            company_website = request.form['company_website']
            company_phone = request.form['company_phone']
            contact_name = request.form['contact_name']
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
            insert_sql = "INSERT INTO company (company_name, company_address, company_website, company_phone, contact_name, company_logo) VALUES (%s, %s, %s, %s, %s, %s)"

            cursor = db_conn.cursor()
            try:
                cursor.execute(insert_sql, (company_name, company_address, company_website, company_phone, contact_name, file_urls_string))
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
        cursor.execute("SELECT company_name, company_address, company_website, company_phone, contact_name, company_logo FROM company")
        companies = cursor.fetchall()
        print(companies)  # Add this line for debugging
        cursor.close()
        return render_template('CompanyList.html', companies=companies)
    except Exception as e:
        print("An error occurred while fetching company data.")
        print("Error:", str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
