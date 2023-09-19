from flask import Flask, render_template, request,render_template, redirect, url_for, flash
from pymysql import connections
import os
import boto3
from config import *

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
table = 'submit_form'


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('Home.html')

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

        # Updated SQL statement
        insert_sql = "INSERT INTO submit_form (company_name, company_address, allowance) VALUES (%s, %s, %s)"
        
        cursor = db_conn.cursor()
        
        if not any(file.filename for file in uploaded_files):
            return "Please select a file"

        # Process the uploaded files and upload to S3 (this part may be expanded as per your need)
        try:
            cursor.execute(insert_sql, (company_name, company_address, allowance))
            db_conn.commit()
        finally:
            cursor.close()

        print("submit_form Submmited Successfully")
    

    # Render the form page. You can also return a template if you have one.
    return render_template('SubmitInternshipForm.html')  # Replace with your template name



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

