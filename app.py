from flask import Flask, request, jsonify, make_response, Response
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Amm905304ar@localhost/codegrapgers_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class register(db.Model):
    __tablename__ = 'register'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.String(50), unique=True)
    firstName = db.Column(db.String(100),  nullable=False)
    lastName = db.Column(db.String(), nullable=True)
    email = db.Column(db.String(), unique=True,  nullable=False)
    username = db.Column(db.String(), unique=True,
                         nullable=False)
    password = db.Column(db.String(),  nullable=False)

    def __init__(self, user_id, firstName, lastName, email, username, password):
        self.user_id = user_id
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.username = username
        self.password = password


class job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer(), primary_key=True)
    jobTitle = db.Column(db.String(200),  nullable=False)
    jobDescription = db.Column(db.String(),  nullable=False)
    jobRate = db.Column(db.Float(),  nullable=False)
    latitude = db.Column(db.String(),  nullable=False)
    longitude = db.Column(db.String(),  nullable=False)
    isActive = db.Column(db.Boolean(),  nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('register.user_id'))
    jobCreated = db.Column(db.DateTime(),  nullable=False)

    def __init__(self, jobTitle, jobDescription, jobRate, latitude, longitude, isActive, user_id, jobCreated):
        self.jobTitle = jobTitle
        self.jobDescription = jobDescription
        self.jobRate = jobRate
        self.latitude = latitude
        self.longitude = longitude
        self.isActive = isActive
        self.user_id = user_id
        self.jobCreated = jobCreated

    def json_job(self):
        return{'id': self.id, 'jobTitle': self.jobTitle, 'jobDescription': self.jobDescription, 'jobRate': self.jobRate, 'latitude': self.latitude, 'longitude': self.longitude, 'isActive': self.isActive, 'user_id': self.user_id, 'jobCreated': self.jobCreated}

    def add_job(_jobTitle, _jobDescription, _jobRate, _latitude, _longitude, _isActive, _user_id, _jobCreated):
        new_job = job(jobTitle=_jobTitle, jobDescription=_jobDescription, jobRate=_jobRate, latitude=_latitude,
                      longitude=_longitude, isActive=_isActive, user_id=_user_id, jobCreated=_jobCreated)
        db.session.add(new_job)
        db.session.commit()

    def get_all_jobs():
        '''function to get all jobs in our database'''
        return [job.json_job(job) for jobs in job.query.all()]

    def get_job(_id):
        return [job.json_job(job.query.filter_by(id=_id).first())]

    def update_job(_id, _jobTitle, _jobDescription, _jobRate, _latitude, _longitude, _isActive, _user_id, _jobCreated):
        job_to_update = job.query.filter_by(id=_id).first()
        job_to_update.jobTitle = _jobTitle
        job_to_update.jobDescription = _jobDescription
        job_to_update.jobRate = _jobRate
        job_to_update.latitude = _latitude
        job_to_update.longitude = _longitude
        job_to_update.isActive = _isActive
        job_to_update.user_id = _user_id
        job_to_update.jobCreated = _jobCreated
        db.session.commit()

    def delete_job(_id):
        job.query.filter_by(id=_id).delete()
        db.session.commit()


@app.route('/job', methods=['GET'])
def get_jobs():
    '''Function to get all the jobs in the database'''
    return jsonify({'Jobs': job.get_all_jobs()})


@app.route('/jobs/<int:id>', methods=['GET'])
def get_job_by_id(id):
    return_value = job.get_job(id)
    return jsonify(return_value)


@app.route('/job', methods=['POST'])
def add_job():
    '''Function to add new job to our database'''
    request_data = request.get_json()
    job.add_job(request_data["jobTitle"], request_data["jobDescription"],
                request_data["jobRate"], request_data["latitude"],
                request_data["longitude"], request_data["isActive"],
                request_data["user_id"], request_data["jobCreated"])
    response = Response("job added", 201, mimetype='application/json')
    return response


@app.route('/job/<int:id>', methods=['PUT'])
def update_job(id):
    '''Function to edit job in our database using job id'''
    request_data = request.get_json(force=True)
    job.update_job(id, request_data["jobTitle"], request_data["jobDescription"],
                   request_data["jobRate"], request_data["latitude"],
                   request_data["longitude"], request_data["isActive"],
                   request_data["user_id"], request_data["jobCreated"])
    response = Response("Job Updated", status=200,
                        mimetype='application/json')
    return response


@app.route('/job/<int:id>', methods=['DELETE'])
def remove_job(id):
    '''Function to delete job from our database'''
    job.delete_job(id)
    response = Response("job Deleted", status=200, mimetype='application/json')
    return response


def token_required(f):
    @ wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing !!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = register.query\
                .filter_by(user_id=data['user_id'])\
                .first()
        except:
            return jsonify({
                'message': 'Token is invalid !!'
            }), 401
        return f(current_user, *args, **kwargs)

    return decorated


@ app.route('/users', methods=['GET'])
@ token_required
def get_all_users(current_user):
    if request.method == 'GET':
        users = register.query.all()
        output = []
        for user in users:
            curruser = {}
            curruser['user_id'] = user.user_id
            curruser['firstName'] = user.firstName
            curruser['lastName'] = user.lastName
            curruser['email'] = user.email
            curruser['username'] = user.username
            curruser['password'] = user.password
            output.append(curruser)
        return jsonify({'users': output})


@ app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        auth = request.form

        if not auth or not auth.get('email') or not auth.get('password'):
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
            )

        user = register.query\
            .filter_by(email=auth.get('email'))\
            .first()

        if not user:
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
            )

        if check_password_hash(user.password, auth.get('password')):
            token = jwt.encode({
                'user_id': user.user_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
            }, app.config['SECRET_KEY'])

            return make_response(jsonify({'token': token.decode('UTF-8')}), 201)
        return make_response(
            'Could not verify',
            403,
            {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
        )


@ app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username, email = data.get('username'), data.get('email')
        firstName, lastName = data.get('firstName'), data.get('lastName')
        password = data.get('password')

        user = register.query\
            .filter_by(email=email)\
            .first()
        if not user:
            user = register(
                user_id=str(uuid.uuid4()),
                firstName=firstName,
                lastName=lastName,
                username=username,
                email=email,
                password=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()

            return make_response('Successfully registered.', 201)
        else:
            return make_response('User already exists. Please Log in.', 202)


if __name__ == "__main__":
    app.run(debug=True)
