from flask import Flask, render_template, request, redirect, url_for
from pymysql import connections
from config import *

app = Flask(__name__)

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)

table = 'company'  # Assuming your table is named 'company'

@app.route("/", methods=['GET'])
def home():
    # Fetch company records from the database
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, company_name, company_address FROM {}".format(table))
    companies = cursor.fetchall()
    cursor.close()
    return render_template('company_approval.html', companies=companies)

@app.route("/approve/<int:company_id>", methods=['POST'])
def approve_company(company_id):
    # Update the company status to 'approved' in the database
    cursor = db_conn.cursor()
    cursor.execute("UPDATE {} SET status = 'approved' WHERE id = %s".format(table), (company_id,))
    db_conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route("/reject/<int:company_id>", methods=['POST'])
def reject_company(company_id):
    # Update the company status to 'rejected' in the database
    cursor = db_conn.cursor()
    cursor.execute("UPDATE {} SET status = 'rejected' WHERE id = %s".format(table), (company_id,))
    db_conn.commit()
    cursor.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
