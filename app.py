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

@app.route('/submitform', methods=['GET', 'POST'])
def submit_form():
    if request.method == 'POST':
        company_name = request.form['company_name']
        company_address = request.form['company_address']
        allowance = request.form['allowance']
        # uploaded_files = request.files.getlist('files[]')

        # Process the text data as per your needs, for example, store in a database.
        # ...

        # Save the uploaded files
        # for file in uploaded_files:
        #     file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        #     file.save(file_path)

        # flash('Form submitted successfully!', 'success')
        # return redirect(url_for('submit_form'))

    # Render the form page. You can also return a template if you have one.
    return render_template('SubmitInternshipForm.html')  # Replace with your template name



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

