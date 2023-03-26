# from flask import Flask,jsonify,request
from flask import Flask,jsonify,request
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import jwt
import pandas as pd
from datetime import datetime
from datetime import date

from flask_socketio import SocketIO, emit, join_room


import os


app=Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads/"
# app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}
# app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:' '@localhost/trkleads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
## database connection
app.secret_key='secretkey'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''

app.config['MYSQL_DB']='trkleads'
mysql=MySQL(app)
# connection code END  
socketio = SocketIO(app, cors_allowed_origins="*")
@app.after_request
def add_cors_headers(response):
    if 'HTTP_ORIGIN' in request.headers:
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']

    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
    if 'HTTP_ORIGIN' in request.headers:
        response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']

    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response
CORS(app, resources={r"/api/*": {"origins": "http://localhost:8080/", "headers": ["content-type"]}})
CORS(app)
# CORS(app, origins=['http://127.0.0.1:5000/api/post_data','http://172.16.33.244:5000','http://127.0.0.1:5000/branches', 'http://localhost:8080/','http://172.16.33.244:8080/','http://localhost:8080/reg'],supports_credentials=True)

# profile image uploading code 
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/uploadimage", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        print("filenothre")
        return jsonify({"success": False, "error": "No file provided"})
      
    file = request.files["file"]
    if file.filename == "":
        print("nofileselected")
        return jsonify({"success": False, "error": "No file selected"})
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        user_id = request.form["user_id"]  # You'll need to modify this to get the user ID from your front-end
        print(filename)
        # mycursor = mydb.cursor()
        cur=mysql.connection.cursor()
        sql = "INSERT INTO user_profile_pictures (user_id, filename) VALUES (%s, %s)"
        val = (user_id, filename)
        cur.execute(sql,val)
        cur.connection.commit()
        return jsonify({"success": True, "filename": filename})
    else:
        return jsonify({"success": False, "error": "Invalid file type"})
#  end of profile upload code

#  login logout 
# Define the user 
# login functionality checking and rendering to admin page
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    name = data['name']
    password = data['password']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE name = %s AND password = %s", (name, password))
    user = cur.fetchone()
    if user:
        role = user[5] 
        if role=='admin':
             print(role)
             token=jwt.encode({'name':name},app.secret_key)
             user_data={'status':'success','role':role,'token':token}
             print(user_data)
             return jsonify(user_data)
           
        
        elif role == 'manager':
            cur.execute("SELECT name FROM branch WHERE manager = %s", (name,))
            bname= cur.fetchone()
            print(bname)
            print(name)
            token = jwt.encode({'name': name}, app.secret_key)
            user_data = {'status': 'success', 'role': role, 'token': token, 'branch':bname[0],'manager':name}
            return jsonify(user_data)
        elif role=='emp':
            cur.execute("SELECT branch FROM employees WHERE name = %s", (name,))
            branch= cur.fetchone()
            print(branch)
            print(name)
            token = jwt.encode({'name': name}, app.secret_key)
            user_data = {'status': 'success', 'role': role, 'token': token, 'branch':branch,'emp_name':name}
            return jsonify(user_data)
            
            print("else block")
        # token = jwt.encode({'name': name}, app.secret_key)
        # user_data = {'status': 'success', 'role': role, 'token': token, 'branch':'name'}
        # return jsonify(user_data)
    else:
        return jsonify({'status': 'failed'}), 401
# @app.route('/api/login', methods=['POST'])
# def login():
    # data = request.get_json()
    # name = data['name']
    # password = data['password']
    # cur = mysql.connection.cursor()
    # cur.execute("SELECT * FROM employees WHERE name = %s AND password = %s", (name, password))
    # user = cur.fetchone()
    # if user:
    #     role = user[5] 
    #     if role == 'admin':
    #         print(role)
    #         token = jwt.encode({'name':name}, app.secret_key)
    #         user_data = {'status':'success', 'role':role, 'token':token}
    #         print(user_data)
    #         return jsonify(user_data)
    #     elif role == 'manager':
    #         cur.execute("SELECT name FROM branch WHERE manager = %s", (name,))
    #         branch_name = cur.fetchone()
    #         print(branch_name)
    #         token = jwt.encode({'name': name}, app.secret_key)
    #         user_data = {'status': 'success', 'role': role, 'token': token, 'branch_name': branch_name}
    #         return jsonify(user_data)
    #     elif role == 'emp':
    #         cur.execute("SELECT branch FROM employees WHERE name = %s", (name,))
    #         branch_name = cur.fetchone()[0]
    #         print(branch_name)
    #         print(name)
    #         cur.execute("SELECT manager FROM branch WHERE name = %s", (branch_name,))
    #         manager_name = cur.fetchone()[0]
    #         print(manager_name)
    #         token = jwt.encode({'name': name}, app.secret_key)
    #         user_data = {'status': 'pending', 'role': role, 'token': token, 'branch_name': branch_name, 'emp_name': name, 'manager_name': manager_name}
    #         cur.execute("INSERT INTO login_requests (employee_name, branch_name, manager_name) VALUES (%s, %s, %s)", (name, branch_name, manager_name))
    #         mysql.connection.commit()
    #         print("Login request sent to manager")
    #         return jsonify(user_data)
    # else:
    #     return jsonify({'status': 'failed'}), 401



          #  END OF LOGIN  ##
###adding JWt token functionality ######################
@app.route('/api/protected', methods=['GET'])
def protected():
    # check for token in headers
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 401
    try:
        # decode token
        data = jwt.decode(token, app.secret_key)
        return jsonify({'message': 'Access granted'})
    except:
        return jsonify({'message': 'Invalid token'}), 401

    ##                       End of JWT                                       ###
# adding language
@app.route('/api/getlanguage',methods=['GET'])
def fetchlanguage():
     cur=mysql.connection.cursor()
     cur.execute("SELECT language FROM Language")
     languages= [row[0] for row in cur.fetchall()]
     print(languages)
     cur.connection.commit()
     cur.close()
     return jsonify(languages)


@app.route('/api/postlanguage',methods=['POST'])
def addlanguage():
    data=request.get_json()
    print(data['language'])
    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO Language (language) VALUES (%s)", (data['language'],))
    cur.execute("SELECT language FROM Language")
    # language=cur.fetchall()
    # print(language)
    languages=[row[0] for row in cur.fetchall()]
    # languages = cur.fetchall()
   
    # language_list = []
    # for language in languages:
    #     language_list.append(language)
    print(languages)
    cur.connection.commit()
    cur.close()
    return jsonify(language=languages)
@app.route('/getlanguages',methods=['GET'])
def getlanguages():
    cur=mysql.connection.cursor()
    cur.execute("SELECT language FROM Language")
    languages=[row[0] for row in cur.fetchall()]
    cur.connection.commit()
    cur.close()
    return jsonify(language=languages)
    
    
# end of adding language
# adding leads to the database code
@app.route('/add/leads',methods=["POST"])
def add_leads():
         file=request.files['file']
         language = request.args.get('language')

         if not file:
            return jsonify({'message':'No file found'})
         df=pd.read_csv(file )
         num_rows = len(df.index)
         cur=mysql.connection.cursor()
         for mobile_number in df.iloc[:, 0]:
             cur.execute('INSERT INTO leads (mobile_number, language) VALUES (%s, %s)', (mobile_number, language))

            # cur.execute('INSERT INTO leads (mobile_number,language) VALUES (%s,%s)', (mobile_number,language))
         cur.connection.commit()
         cur.close()
  
         return jsonify({'message': 'Leads uploaded successfully','num_rows':num_rows})
#   END of adding leads code
# counting leads from db

       
    
     
# end of countleads

# employee fetching code
@app.route('/getemployees', methods=['GET'])
def get_employees():
    branch = request.args.get('branch')
    print(branch)
    # data=request.get_json()
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT name FROM employees WHERE branch=%s and role='emp'", (branch,))
        data = cur.fetchall()
        print(data)
        cur.close()
        return jsonify({'employees': data})
    except Exception as e:
        print("Error retrieving employees:", e)
        return jsonify({'error': 'Unable to retrieve employees. Please try again later.'}), 500


#  end of code

@app.route('/employees', methods=['GET'])
def get_employeenames():
    
    cur=mysql.connection.cursor()
    cur.execute("SELECT name from employees")
    employees=[row[0] for row in cur.fetchall()]
    print(employees)
    cur.connection.commit()
   
    cur.close()
    return jsonify(employees=employees)

@app.route('/employees/<string:role>', methods=['GET'])
def get_employees_by_role(role):
    if role == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees where role!='admin'")
        rows = cur.fetchall()
        cur.close()
        return jsonify(employees=rows)
    else:
        branch_name = request.args.get('branchname')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employees WHERE branch=%s", (branch_name,))
        rows = cur.fetchall()
        cur.close()
        return jsonify(employees=rows)

@app.route('/adleadscount', methods=['GET'])
def get_employee_leads():
    cur = mysql.connection.cursor()

    # Get employee name and branch name
    cur.execute("SELECT emp_name, branch FROM leads_status")
    leads = cur.fetchall()

    employee_leads = []
    for lead in leads:
        empname = lead[0]
        branchname = lead[1]

        # Get total assigned leads count
        cur.execute("SELECT COUNT(*) FROM assigned_leads WHERE emp_name=%s", (empname,))
        total_leads = cur.fetchone()[0]

        # Get completed leads count
        cur.execute("SELECT COUNT(*) FROM leads_status WHERE emp_name=%s AND status='Completed'", (empname,))
        completed_leads = cur.fetchone()[0]
        print(completed_leads)
        # Calculate remaining leads
        remaining_leads = total_leads - completed_leads

        employee_leads.append({
            'empname': empname,
            'branchname': branchname,
            'total_leads': total_leads,
            'completed_leads': completed_leads,
            'remaining_leads': remaining_leads
        })

    cur.close()

    return jsonify(employee_leads=employee_leads)





# @app.route('/apiget/allemployees', methods=['GET'])
# def get_allemployeenames():
#     # role = request.args.get('role')
#     # branch = request.args.get('branch')
#     data=request.get_json()
#     role=data['role']
   
#     print(role)
#     cur = mysql.connection.cursor()
#     allemployees=None
    
#     if role == 'admin':
#         cur.execute("SELECT * from employees where role!='admin'")
#         allemployees = cur.fetchall()
#     elif role == 'manager':
#         branch=data['branch']
#         cur.execute("SELECT * from employees where role!='admin' and branch=%s", (branch,))
#         allemployees = cur.fetchall()
#     else:
#         return jsonify(message='Invalid role specified'), 400

#     cur.connection.commit()
#     cur.close()

#     return jsonify(employee=allemployees, headers={'Content-Type': 'application/json'})



#inserting sample data to users table

@app.route('/insertemp',methods=["POST"])
def insert():
    data=request.get_json()
    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO employees ( name,email,password,branch) VALUES ( %s,%s,%s,%s)", ( data['name'],data['email'],data['password'],data['branch']))
    cur.connection.commit()
    cur.close()
    return "Data posted"
# fetching employees data
@app.route('/addmanager', methods=["POST"])
def addmanager():
    data = request.get_json()
    name = data['name']
    branch_name=data['branchName']
    
    cur = mysql.connection.cursor()
    # cur.execute("UPDATE branch SET manager={'name'} WHERE name=%s", (branch_name,))
    cur.execute(f"UPDATE branch SET manager='{name}' WHERE name=%s", (branch_name,))

    cur.execute("UPDATE employees SET role='manager' WHERE name=%s", (name,))
    mysql.connection.commit()
    cur.close()
    return "Data posted"

# assigning manager

# end of assigninig manager code

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch_name = db.Column(db.String(50))
    employee_name = db.Column(db.String(50))
    target_type = db.Column(db.String(50))
    leads = db.Column(db.Float)
    language = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float)
    month = db.Column(db.String(50), default=None)

class FuturePayments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clientname = db.Column(db.String(50))
    empname = db.Column(db.String(50))
    date = db.Column(db.Date)
    futuredate = db.Column(db.Date)
    status = db.Column(db.String(50))
    payment = db.Column(db.Float)
    mobilenumber = db.Column(db.String(15))
class Payment_clients(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    empname = db.Column(db.String(100))
    branch = db.Column(db.String(100))
    date = db.Column(db.Date)
    clientname = db.Column(db.String(100))
    amount = db.Column(db.Float)
    received_amount = db.Column(db.Float)
    amount_received_to = db.Column(db.String(100))
    amount_sent_to = db.Column(db.String(100))
    payment_type = db.Column(db.String(100))
    remaining_amount = db.Column(db.Float)
    status = db.Column(db.String(100))
    client_type = db.Column(db.String(100))
    language = db.Column(db.String(100))

class Leads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mobile_number = db.Column(db.String(255))
    language = db.Column(db.String(50))
class LeadsRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    no_of_leads = db.Column(db.Integer)
    language = db.Column(db.String(50))
    date_of_request = db.Column(db.Date)
    emp_name = db.Column(db.String(50))
    status = db.Column(db.String(255), nullable=False, default='pending')
    branch_name = db.Column(db.String(50))


class AssignedLead(db.Model):
    __tablename__ = 'assigned_leads'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    emp_name = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    lead_status = db.relationship('LeadStatus', backref='assigned_lead', lazy=True)

class LeadStatus(db.Model):
    __tablename__ = 'leads_status'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('assigned_leads.id'), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    emp_name = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50))
    status = db.Column(db.String(255), default='pending')

    
class ClientDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20))
    number = db.Column(db.String(20))
    alternate_number = db.Column(db.String(20))
    amount = db.Column(db.Float)
    name = db.Column(db.String(50))
    language = db.Column(db.String(10))
    branch = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    empname = db.Column(db.String(50))
def to_dict(self):
        return f"<ClientDetails(id='{self.id}', name='{self.name}', amount='{self.amount}')>"
class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    manager = db.Column(db.String(50), nullable=True, default='')


    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'location': self.location ,'manager':self.manager}

class Manager(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Employees(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False, default='emp')

    def to_dict(self):
          return {
              'id': self.id,
              'name': self.name,
              'email': self.email,
              'password': self.password,
              'branch': self.branch,
              'role': self.role
              
              
          }
class Language(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(255), nullable=False)
    def to_dict(self):
          return {
              'id': self.id,
              'name': self.language,
              
              
              }
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.relationship('UserProfilePicture', backref='user', uselist=False)

class UserProfilePicture(db.Model):
    __tablename__ = 'user_profile_pictures'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
with app.app_context():
    db.create_all()
# backend for adding branch and fetching users data
@app.route('/apiget/branches', methods=['GET'])
def get_branches():
    branches = Branch.query.all()
    branches=[branch.to_dict() for branch in branches]
    # print(branches)
    return jsonify(branches), 200




@app.route('/apipost/branches', methods=['POST'])
def add_branch():
    data = request.get_json()
   
    name=data["name"]
   
    branch = Branch( location=data["location"],name=name)
   
    db.session.add(branch)
    db.session.commit()
    return jsonify(branch.to_dict()), 201
# fetching only branches name AND ID
@app.route('/apiget/branchename', methods=['GET'])
def get_branchename():
   
    cur=mysql.connection.cursor()
    cur.execute("SELECT name from branch")
    cur.connection.commit()
    branch=[row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify(branch=branch)


# end of branch name fetching

#get data of employees based on the id from managers db
@app.route('/managers/<int:m_id>', methods=['GET'])
def get_managersbyid(m_id):
     print(m_id)
     emp =Manager.query.get(m_id)
     if emp:
         return jsonify({'name':emp.name}),200
     return jsonify({'error':'employee not found'}),404
    
           
     



# leads data counting and displaying
@app.route('/api/leads/count')
def get_lead_count():
    cursor = mysql.connection.cursor()
    query = "SELECT COUNT(mobile_number) FROM leads"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    return {'count': count}

   
    # return jsonify({'count': count})
@app.route('/api/leads/assign', methods=['POST'])
def assign_leadsto():
    # Get the count, branch_name, language, and emp_name from the request data
    count = int(request.json['count'])
    branch_name = request.json['branch_name']
    language = request.json['language']
    emp_name = request.json['emp_name']

    cursor = mysql.connection.cursor()

    # Get the mobile numbers from the leads table that haven't been assigned to any branch and language yet
    query = "SELECT DISTINCT id,mobile_number FROM leads WHERE mobile_number NOT IN (SELECT mobile_number FROM assigned_leads) AND language=%s ORDER BY mobile_number ASC LIMIT %s"
    cursor.execute(query, (language, count,))
    leads = cursor.fetchall()
    print(leads[0])
    # Check if enough leads are available
    if len(leads) < count:
        return jsonify({'message': 'Not enough leads available to assign.'}), 400

    # Get the id of the employee
    query = "SELECT name FROM employees WHERE name=%s"
    cursor.execute(query, (emp_name,))
    emp_id = cursor.fetchone()

    if not emp_id:
        return jsonify({'message': 'Employee not found.'}), 404

    assigned_count = 0
    for lead in leads:
        if assigned_count == count:
            break

        # Check if the lead is already assigned to any employee
        query = "SELECT mobile_number FROM assigned_leads WHERE mobile_number=%s"
        cursor.execute(query, (lead[1],))
        assigned_leads = cursor.fetchall()

        if assigned_leads:
            continue

        # Assign the lead to the specified employee, branch, and language
        query = "INSERT INTO assigned_leads (lead_id ,mobile_number, emp_name, branch, language) VALUES (%s, %s, %s, %s,%s)"
        values = (lead[0],lead[1], emp_id[0], branch_name, language)
        cursor.execute(query, values)
        assigned_count += 1

    # Commit the changes to the database and return a success message
    cursor.connection.commit()
    return jsonify({'message': f'Successfully assigned {assigned_count} leads to {emp_name}.'}), 200


# @app.route('/api/leads/branch',methods=['GET'])
# def get_leads():
#     cursor = mysql.connection.cursor()
#     query = "SELECT mobile_number FROM assigned_leads WHERE branch_name='vizag-1'"
#     cursor.execute(query)
#     count = cursor.fetchall()
#     print(count)
#     return jsonify(leads=count)
    
    


# Define the route for the endpoint

#  final assigning leads to the
# @app.route('/api/leads/assign', methods=['POST'])
# def assign_leads():
#     # Get the count and branch_name from the request data
#     count = int(request.json['count'])
#     branch_name = request.json['branch_name']

#     cursor = mysql.connection.cursor()

#     # Get the mobile numbers from the leads table that haven't been assigned to any branch yet
#     query = "SELECT DISTINCT mobile_number FROM leads WHERE mobile_number NOT IN (SELECT mobile_number FROM assigned_leads) ORDER BY mobile_number ASC LIMIT %s"
#     cursor.execute(query, (count,))
#     leads = cursor.fetchall()

#     # Check if enough leads are available
#     if len(leads) < count:
#         return jsonify({'message': 'Not enough leads available to assign.'}), 400

#     assigned_count = 0
#     for lead in leads:
#         if assigned_count == count:
#             break

#         # Assign the lead to the specified branch
#         query = "INSERT INTO assigned_leads (mobile_number, branch_name) VALUES (%s, %s)"
#         values = (lead[0], branch_name)
#         cursor.execute(query, values)
#         assigned_count += 1

#     # Commit the changes to the database and return a success message
#     cursor.connection.commit()
#     return jsonify({'message': f'Successfully assigned {assigned_count} leads to {branch_name}.'}), 200


# e nde of final



   
# end of assigning leads to the branch







#  end of assigned leads table code
# interested leads
# @app.route('/api/leads/assign/emp',methods=['POST'])
# def assigntoemp():
   # Get the employee name, branch name, and count from the request data
    # emp_name = request.json['emp_name']
    # branch_name = request.json['branch_name']
    # count = int(request.json['count'])

    # cursor = mysql.connection.cursor()

    # # Check if the branch exists
    # query = "SELECT name FROM branch WHERE name = %s"
    # cursor.execute(query, (branch_name,))
    # result = cursor.fetchone()
    # if result is None:
    #     return jsonify({'message': 'Branch does not exist.'}), 400

    # # Get the mobile numbers from the assigned_leads table that belong to the specified branch
    # query = "SELECT  DISTINCT mobile_number FROM assigned_leads WHERE branch_name = %s ORDER BY mobile_number ASC LIMIT %s"
    # cursor.execute(query, (branch_name,count))
    # assigned_leads = cursor.fetchall()

    # # Get the mobile numbers from the leads table that haven't been assigned to any branch yet
    # # query = "SELECT mobile_number FROM leads WHERE mobile_number NOT IN (SELECT mobile_number FROM assigned_leads) ORDER BY mobile_number ASC"
    # # cursor.execute(query)
    # # unassigned_leads = cursor.fetchall()

    # # # Check if enough leads are available
    # # available_count = min(len(assigned_leads) + len(unassigned_leads), count)
    # # if available_count < count:
    # #     return jsonify({'message': 'Not enough leads available to assign.'}), 400

    # # assigned_count = 0
    # for lead in assigned_leads:
    #     # if assigned_count == count:
    #     #  break

    # # Assign the lead to the specified employee and branch
    #    query = "UPDATE assigned_leads SET emp_name =%s WHERE branch_name =%s AND mobile_number =%s"
    #    values = (emp_name, branch_name, lead[0])
    #    print(values)
    #    cursor.execute(query, values)

    # #    assigned_count += 1

    #    mysql.connection.commit()

    # return jsonify("done")

@app.route('/leads_request',methods=['POST'])
def lead_request():
    data = request.get_json()
    lang = data['language']
    emp_name = data['emp_name']
    noofleads = data['count']
    cur = mysql.connection.cursor()
    cur.execute("SELECT branch from employees where name=%s", (emp_name,))
    branch_name = cur.fetchone()[0]
    
    today = date.today()
    formatted_date = today.strftime("%Y-%m-%d")
    tdate=formatted_date
    print(formatted_date)
    cur.execute("INSERT INTO leads_request (no_of_leads, language, date_of_request, emp_name, branch_name) VALUES (%s, %s, %s, %s, %s)", (noofleads, lang,tdate, emp_name, branch_name))
    
    cur.connection.commit()
    cur.close()
    return jsonify("done")

@app.route('/getrequests',methods=['GET'])

def getlead_requests():
    
   
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leads_request where status='pending'")
    requested_leads=cur.fetchall()
    
    
    cur.connection.commit()
    cur.close()
    return jsonify(leads=requested_leads)
@app.route('/updaterequest',methods=['POST'])
def updatestatus():
    cur = mysql.connection.cursor()
    data=request.get_json()
    status=data['status']
    name=data['name']
    count=data['count']
    print(status)
    
    cur.execute("UPDATE `leads_request` SET `status`=%s WHERE emp_name=%s and no_of_leads=%s ",(status,name,count))
    cur.execute("SELECT * FROM leads_request where status=%s",(status,))
    updateddata=cur.fetchall()
    
    
    cur.connection.commit()
    cur.close()
    return jsonify(leads=updateddata)
@app.route('/updaterequest',methods=['GET'])
def getcompleted():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leads_request where status='completed'")
    updateddata=cur.fetchall()
    print(updateddata)
    cur.connection.commit()
    cur.close()
    return jsonify(leads=updateddata)
@app.route('/prevrequest',methods=['POST'])
def prevrequests():
    data=request.get_json()
    name=data['name']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM leads_request where  emp_name=%s ",(name,))
    updateddata=cur.fetchall()
    print(updateddata)
    cur.connection.commit()
    cur.close()
    return jsonify(leads=updateddata)

@app.route('/fetchleads',methods=['GET'])

def fetchlead_requests():
    # getting the count of leads which are left after nothing but remaining leads from leads table used in admin leadrequestspage
   
    cur = mysql.connection.cursor()
    cur.execute("SELECT mobile_number FROM leads WHERE mobile_number NOT IN (SELECT mobile_number FROM assigned_leads)")
    mobile_numbers = [row[0] for row in cur.fetchall()]
    # print(count)
    
    cur.connection.commit()
    cur.close()
    return jsonify(leads=mobile_numbers)



@app.route('/todaycalls', methods=['GET'])
def today_calls():
    from datetime import date
    today = date.today()

    empname = request.args.get('name')
    if not empname:
        return jsonify(error='Employee name is required'), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM client_details WHERE date=%s AND empname=%s", (today, empname))
    lead_count = cur.fetchone()[0]
    cur.close()
    return jsonify(count=lead_count)

# @app.route('/assign
@app.route('/assigned_leads_count', methods=['GET'])
def completed():
    emp_name = request.args.get('emp_name')
    branch_name = request.args.get('branch_name')
    if emp_name:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE mobile_number IN (SELECT mobile_number from leads_status) and emp_name=%s",(emp_name,))
        lead_count = cur.fetchone()
        cur.close()
        if lead_count:
            return jsonify(count=lead_count[0])
        else:
            return "No leads assigned to the employee."
    elif branch_name:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE mobile_number IN (SELECT mobile_number from leads_status) and branch=%s",(branch_name,))
        lead_count = cur.fetchone()
        print(lead_count)
        cur.close()
        if lead_count:
            return jsonify(count=lead_count[0])
        else:
            return "No leads assigned to the branch."
    else:
        return "Employee or branch name not provided."

@app.route('/assignesleads', methods=['GET'])
def assignedcount():
  emp_name = request.args.get('emp_name')
#   emp_name='rahul'
#   print(emp_name)
  if emp_name is not None:
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM assigned_leads WHERE emp_name=%s",(emp_name,))
    lead_count = cur.fetchone()
    print(lead_count)
    cur.close()
    return jsonify(count=lead_count)
  else:
    return "Employee name not provided"



@app.route('/leads_status', methods=['GET'])
def lead_status():
    status = request.args.get('status')
    empname = request.args.get('empname')


    cur = mysql.connection.cursor()
    emp = None
    admin=None
    if empname:
      cur.execute("SELECT COUNT(mobile_number) from leads_status where status=%s AND emp_name=%s", (status, empname,))
      emp=cur.fetchone()[0]
      
       
    else:
   
         cur.execute("SELECT COUNT(mobile_number) from leads_status where status=%s", (status,))
         admin = cur.fetchone()[0]
    print(lead_status)
    cur.connection.commit()
    cur.close()
    return jsonify({'emp':emp,'admin':admin})

#requestes for employee
@app.route('/getleads/emp', methods=['GET'])
def assignedleads():
    name = request.args.get('name')
    print(name)
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, mobile_number,language,branch FROM assigned_leads WHERE mobile_number NOT IN (SELECT mobile_number FROM leads_status) AND emp_name =%s ", (name,))
    leads = cur.fetchall()
    # cur.execute("SELECT mobile_number from leads_status where emp_name=%s",(name,))
    
    lead= cur.fetchall()
    print(leads)
    print(lead)
    cur.connection.commit()
    cur.close()
    return jsonify(leads=leads)
# @app.route('/leads/status', methods=['GET','POST'])
# def leadsstatus():
#     data=request.get_json()
    
#     name=data['name']
#     status=data['status']
#     print(status)
#     print(name)
#     if (name):  
#           cur = mysql.connection.cursor()
#           cur.execute("SELECT * from client_details where empname=%s AND status=%s ",(name,status))
#           leads = cur.fetchall()
#           cur.connection.commit()
#           cur.close()
#           return jsonify(leads=leads)
#     else:
#         return "done admon"
@app.route('/leads/status', methods=['GET', 'POST'])
def leadsstatus():
    try:
        data = request.get_json()
        name = data.get('name')
        status = data.get('status')
        if not status:
            return jsonify(error='Status is required'), 400

        cur = mysql.connection.cursor()
        if name:
            # Request is from an employee, fetch leads based on employee name and status
            cur.execute("SELECT * FROM client_details WHERE empname=%s AND status=%s", (name, status))
        else:
            # Request is from an admin, fetch all leads based on status
            cur.execute("SELECT * FROM client_details WHERE status=%s", (status,))
        leads = cur.fetchall()
        cur.connection.commit()
        cur.close()
        return jsonify(leads=leads)
    except Exception as e:
        print(str(e))
        return jsonify(error='Internal server error'), 500

    

@app.route('/updatelead/status', methods=['POST'])
def leadstatusupdate():
    data=request.get_json()
    status=data['status']
    id=data['lead_id']
   
    number=data['number']
    language=data['language']
    date=data['date']
    empname=data['empname']
    name=data['name']
    amount=data['amount']
    altnum=data['alternatenumber']
    branch=data['branch']
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO leads_status (lead_id,mobile_number,status,emp_name,language,branch) VALUES (%s, %s, %s,%s,%s,%s)", (id, number, status,empname,language,branch))
    cur.execute("INSERT INTO client_details (status,number,alternate_number,amount,name,language,date,empname,branch) VALUES (%s,%s, %s, %s,%s,%s,%s,%s,%s)", (status,number,altnum,amount,name,language,date,empname,branch))

    # leads = cur.fetchall()
    cur.connection.commit()
    cur.close()
    return jsonify("done")
# future payments
# @app.route('/future/payments', methods=['GET'])
# def fututrepayments():
#     name = request.args.get('employeeName')
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM future_payments where empname=%s ",(name,))
#     rows = cur.fetchall()
#     cur.close()
#     return jsonify(clients=rows)

# end
# payment from interested clients
# @app.route('/intcl/payments', methods=['GET'])
# def get_payments():
#     name = request.args.get('employeeName')
#     print(name)
    
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM payment_clients where empname=%s ",(name,))
#     rows = cur.fetchall()
#     print(rows)
#     cur.close()
#     return jsonify(clients=rows)
@app.route('/intcl/payments', methods=['GET'])
def get_payments():
    try:
        name = request.args.get('employeeName')
        branch= request.args.get('branch')
        cur = mysql.connection.cursor()
        if name:
            # Request is from an employee, fetch payments based on empname
            cur.execute("SELECT * FROM payment_clients WHERE empname=%s", (name,))
        elif branch:
        # Request is from a manager, fetch payments based on branch name
              cur.execute("SELECT * FROM payment_clients WHERE branch=%s", (branch,))
        else:
            # Request is from an admin, fetch all payments
            cur.execute("SELECT * FROM payment_clients")
        rows = cur.fetchall()
        cur.close()

        return jsonify(clients=rows)
    except Exception as e:
        print(str(e))
        return jsonify(error='Internal server error'), 500

@app.route('/spcl/<role>', methods=['GET'])
def get_special_clients(role):
    if role == 'admin':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM payment_clients WHERE  client_type='special'")
        rows = cur.fetchall()
        cur.close()
        return jsonify(clients=rows)
    elif role == 'manager':
        branch_name = request.args.get('branchName')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM payment_clients WHERE client_type='special' AND branch=%s", (branch_name,))
        rows = cur.fetchall()
        cur.close()
        return jsonify(clients=rows)
    else:
        return jsonify(error='Invalid role'), 400

    
@app.route('/intcl/payments', methods=['POST'])
def payments():
    data=request.get_json()
    date=data['date']
    cname=data['client_name']
    fdate=data['fdate']
    amount=data['amount']
    # received=data['amount']
    receivedto=data['amount_receivedby']
    sendto=data['amount_sentto']
    partial=data['partialamount']
    # print(partial)
    ptype=data['paytype']
    status=data['updatedstatus']
    ctype=data['special']
    empname=data['emp_name']
    branch=data['branch']
    language=data['language']
    number=data['number']
    
    cur = mysql.connection.cursor()
    if ptype =='Partial':
            # print(ptype)
            remaining=amount-int(partial)
            cur.execute("INSERT INTO payment_clients (empname, branch,date,clientname,amount,received_amount,amount_received_to,amount_sent_to,payment_type,remaining_amount,status,client_type,language) VALUES (%s,%s, %s, %s,%s,%s,%s, %s, %s,%s,%s,%s,%s)",
                (empname,branch,date,cname,amount,partial,receivedto,sendto,ptype,remaining,status,ctype,language))
            cur.execute("UPDATE leads_status SET status=%s WHERE mobile_number=%s",(status,number))
            cur.execute("UPDATE client_details SET status=%s WHERE number=%s ",(status,number))
            cur.connection.commit()
            cur.close()
            return jsonify("done")
    elif ptype =='Full':
         print("full")
         remaining=amount-amount
         cur.execute("INSERT INTO payment_clients (empname, branch,date,clientname,amount,received_amount,amount_received_to,amount_sent_to,payment_type,remaining_amount,status,client_type,language) VALUES (%s,%s, %s, %s,%s,%s,%s, %s, %s,%s,%s,%s,%s)",
                (empname,branch,date,cname,amount,amount,receivedto,sendto,ptype,remaining,status,ctype,language))
         cur.execute("UPDATE leads_status SET status=%s WHERE mobile_number=%s",(status,number))
         cur.execute("UPDATE client_details SET status=%s WHERE number=%s",(status,number))
            
    
         cur.connection.commit()
         cur.close()
         return jsonify("done")
    elif ptype =='Future':
         print("future")
         remaining = None
         received = None
         sent_to = None
         cur.execute("INSERT INTO payment_clients (empname, branch,date,clientname,amount,received_amount,amount_received_to,amount_sent_to,payment_type,remaining_amount,status,client_type,language) VALUES (%s,%s, %s, %s,%s,%s,%s, %s, %s,%s,%s,%s,%s)",
                (empname,branch,date,cname,amount,received,received,sent_to,ptype,remaining,status,ctype,language))
         cur.execute("UPDATE leads_status SET status=%s WHERE mobile_number=%s",(status,number))
         cur.execute("UPDATE client_details SET status=%s WHERE number=%s",(status,number))
            
    
         cur.connection.commit()
         cur.close()
         return jsonify("done")
        

# 
@app.route('/emp/target', methods=['GET'])
def emptarget():
    # data = request.get_json()
    emp = request.args.get('empname')
    # Monthly='Monthly',
    # Daily='Daily'
    print(emp)
    date = datetime.today().strftime('%Y-%m-%d')
    current_month = datetime.today().strftime('%B')
    cur = mysql.connection.cursor()
    cur.execute("SELECT amount,leads from target where employee_name=%s and target_type=%s and month=%s", (emp, 'Monthly', current_month))
    m=cur.fetchall()
    cur.execute("SELECT amount,leads from target where employee_name=%s and target_type=%s and date=%s", (emp, 'Daily', date))
    d=cur.fetchall()
    data = {'monthly': m[0], 'daily': d[0]}
    return jsonify(data)

# end of employee requests
# Manager requests#######MANAGER # # # # 3 # # # 3
@app.route('/apiget/branchemployees/<branch>', methods=['GET'])
def get_branch_employees(branch):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE branch = %s", (branch,))
    employees = cur.fetchall()
    cur.execute("SELECT manager FROM branch WHERE name = %s", (branch,))
    manager = cur.fetchone()
    data = {
        'employees': employees,
        'manager': manager
    }
    return jsonify(data)
@app.route('/manager/leadsassigned/<branch>', methods=['GET'])
def get_manager_assignleads(branch):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(mobile_number) FROM assigned_leads WHERE branch = %s", (branch,))
    leads= cur.fetchone()
    print(leads)
    # cur.execute("SELECT manager FROM branch WHERE name = %s", (branch,))
    # manager = cur.fetchone()
    # data = {
    #     'employees': employees,
    #     'manager': manager
    # }
    return jsonify(data=leads)
@app.route('/branch/leads_status',methods=['GET'])
def branch_lead_status():
    # data=request.get_json()
    status = request.args.get('status')
    branhname=request.args.get('branch')
    # print(empname)
    # status=data['status']
    # print(status)
    cur=mysql.connection.cursor()
    cur.execute("SELECT COUNT(mobile_number) from leads_status where status=%s AND branch=%s", (status,branhname,))

    lead_status= cur.fetchone()
    print(lead_status)
    cur.connection.commit()
   
    cur.close()
    return jsonify(count=lead_status)

# END Manager requests#######MANAGER # # # # 3 # # # 3
#admin ####
@app.route('/api/target', methods=['POST'])
def target():
    data = request.get_json()
    branch = data['branch']
    empname = data['emp']
    lan = data['lang']
    month= data['month']
    leads = data['target']
    amount=data['amount']
    ttype = data['targettype']
    date = datetime.today().strftime('%Y-%m-%d')
    
    if ttype == 'Monthly':
        new_target = Target(branch_name=branch, employee_name=empname, target_type=ttype, leads=leads,amount=amount,month=month ,language=lan,date=date)
    else:
        new_target = Target(branch_name=branch, employee_name=empname, target_type=ttype, leads=leads,amount=amount , language=lan,date=date)
    
    db.session.add(new_target)
    db.session.commit()

    return "done"
# end 

if __name__=="__main__":
    app.run(debug=True)
  