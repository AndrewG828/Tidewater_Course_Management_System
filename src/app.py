from db import db
from flask import Flask, request, jsonify, json
from db import User, Assignment, Course, Submission
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError
import uuid


app = Flask(__name__)
db_filename = "cms.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

load_dotenv()

S3_BUCKET = "cmssubmissionfiles"
AWS_REGION = os.getenv("AWS_REGION")
S3_URL = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/"
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

db.init_app(app)
with app.app_context():
    db.create_all()


# your routes here
def success_response(data, code = 200):
    return json.dumps(data, sort_keys=False), code

def failure_response(message, code = 404):
    return json.dumps({"error": message}), code

@app.route("/")
def base():
    return "Hello this is " + os.environ.get("NAME")+ "'s Course Management System. Welcome!"

@app.route("/api/courses/")
def get_all_courses():
    """
    Endpoint for getting all courses
    """
    return success_response({"courses": [c.serialize() for c in Course.query.all()]})

@app.route("/api/courses/", methods=["POST"])
def create_course():
    body = json.loads(request.data)
    if body.get("code") is None or body.get("name") is None: 
        return failure_response("Please provide the course code and/or name", 400)
    new_course = Course(
        code = body.get("code"),
        name = body.get("name")
    )
    db.session.add(new_course)
    db.session.commit()
    return success_response(new_course.serialize(), 201)

@app.route("/api/courses/<int:course_id>/")
def get_course_by_id(course_id):
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("The course does not exist")
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/", methods = ["DELETE"])
def delete_course_by_id(course_id):
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("The course does not exist")
    db.session.delete(course)
    db.session.commit()
    return success_response(course.serialize())

@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    if not body.get("name") or not body.get("netid"):
        return failure_response("User needs a name and netid")
    new_user = User(
        name = body.get("name"),
        netid = body.get("netid")
    )
    db.session.add(new_user)
    db.session.commit()
    return success_response(new_user.serialize())

@app.route("/api/users/")
def get_all_users():
    return success_response({"users":[u.serialize() for u in User.query.all()]})

@app.route("/api/users/<int:user_id>/")
def get_user_by_id(user_id):
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("The user does not exist")
    return success_response(user.serialize())

@app.route("/api/courses/<int:course_id>/add/", methods=["POST"])
def add_user_to_course(course_id):
    course = Course.query.filter_by(id = course_id).first()
    if Course is None:
        return failure_response("This course does not exist")
    body = json.loads(request.data)
    user_id = body.get("user_id")
    user_type = body.get("type")
    if not user_id or not user_type:
        return failure_response("Please enter a user to add and their type (instructor or student)")
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("This user does not exist")
    if user_type == "student":
        if user in course.students:
            return failure_response("User is already in course roster")
        course.students.append(user)
    elif user_type == "instructor":
        if user in course.instructors:
            return failure_response("User is already in instructor roster")
        course.instructors.append(user)
    db.session.commit()
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/drop/", methods=["POST"])
def drop_user_from_course(course_id):
    course = Course.query.filter_by(id = course_id).first()
    if not course:
        return failure_response("This course does not exist")
    body = json.loads(request.data)
    user_id = body.get("user_id")
    user = User.query.filter_by(id = user_id).first()
    if not user:
        return failure_response("User not found")
    if not user in course.students and not user in course.instructors:
        return failure_response("User has not been added to this course")
    if user in course.students:
        course.students.remove(user)
    elif user in course.instructors:
        course.instructors.remove(user)
    db.session.commit()
    return success_response(user.serialize())

@app.route("/api/courses/<int:course_id>/assignment/", methods=["POST"])
def create_assignment(course_id):
    course = Course.query.filter_by(id = course_id)
    if not course:
        return failure_response("This course does not exist")
    body = json.loads(request.data)
    title = body.get("title")
    due_date = body.get("due_date")
    if not title or not due_date:
        return failure_response("Please enter a assignment title and due date"), 400
    new_assignment = Assignment(
        title = title,
        due_date = due_date,
        course_id = course_id
    )    
    db.session.add(new_assignment)
    db.session.commit()
    return success_response(new_assignment.serialize())

@app.route("/api/assignments/<int:assignment_id>/", methods=["POST"])
def update_assignment(assignment_id):
    assignment = Assignment.query.filter_by(id = assignment_id).first()
    if not assignment:
        return failure_response("Assignment not found")
    body = json.loads(request.data)
    if body.get("title"):
        assignment.title = body.get("title")
    if body.get("due_date"):
        assignment.due_date = body.get("due_date")
    db.session.commit()
    return success_response(assignment.serialize())

@app.route("/api/assignments/<int:assignment_id>/submit/", methods=["POST"])
def submission_for_assignment(assignment_id):
    #Parses file
    try:
        user_id = request.form.get("user_id")
        file = request.files.get("content")
        print(user_id)
        #file = request.files.get("content")
        print(file)

        if not file:
            return failure_response("Please provide a file to submit")
        if not user_id:
            return failure_response("please provide a user_id to submit")
        # Generate a unique filename using UUID
        file_key = f"{uuid.uuid4()}-{file.filename}"
        s3.upload_fileobj(
            file,
            S3_BUCKET,
            file_key,
            ExtraArgs={"ACL": "public-read"}  # Makes the file publicly accessible
        )

        file_url = f"{S3_URL}{file_key}"

    except NoCredentialsError:
        return failure_response("AWS credentials not found")
    
    except Exception as e:
        return failure_response(str(e))
    
    assignment = Assignment.query.filter_by(id = assignment_id).first()
    if not assignment:
        return failure_response("Assignment not found")
    course_id = assignment.course_id
    course = Course.query.filter_by(id = course_id).first()
    user = User.query.filter_by(id = user_id).first()
    if user in course.students:
        new_submission =  Submission(
            user_id = user_id,
            content = file_url,
            score = None,
            assignment_id = assignment_id
        )
        db.session.add(new_submission)
        db.session.commit()
        return success_response(new_submission.serialize())
    else:
        return failure_response("This user is not a student in the course and can't submit")
    
@app.route("/api/assignments/<int:assignment_id>/grade/", methods=["POST"])
def grade_submission(assignment_id):
    body = json.loads(request.data)
    submission_id = body.get("submission_id")
    score = body.get("score")
    if not submission_id or not score:
        return failure_response("Please enter a submission to grade and score")
    assignment = Assignment.query.filter_by(id = assignment_id).first()
    if not assignment: 
        return failure_response("Assignment not found")
    submission = Submission.query.filter_by(id = submission_id).first()
    if not submission:
        return failure_response("Submission not found")
    submission.score = score
    db.session.commit()
    return success_response(submission.serialize())

@app.route('/api/schema/<table_name>/', methods=['GET'])
def get_table_schema(table_name):
    """
    Retrieve the schema of a specified table in the database.
    """
    try:
        result = db.engine.execute(f"PRAGMA table_info({table_name})")
        columns = [{"name": row[1], "type": row[2], "nullable": row[3] == 0} for row in result]
        return success_response({"table": table_name, "columns": columns})
    except Exception as e:
        return failure_response(f"Error retrieving schema: {str(e)}")
    
@app.route("/api/submissions/delete/", methods=["DELETE"])
def delete_submission_table():
    try:
        Submission.__table__.drop(db.engine)
        return success_response({"message": "Submissions table dropped successfully."})
    except Exception as e:
        return failure_response(f"Failed to drop submissions table: {str(e)}")


    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
