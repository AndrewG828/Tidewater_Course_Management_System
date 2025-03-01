from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# your classes here
instructor_course_table = db.Table(
    "instructor_course",
    db.Model.metadata,
    db.Column("course.id", db.Integer, db.ForeignKey("courses.id")),
    db.Column("instructor_id", db.Integer, db.ForeignKey("users.id"))
)

student_course_table = db.Table(
    "student_course",
    db.Model.metadata,
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id")),
    db.Column("student_id", db.Integer, db.ForeignKey("users.id"))
)

class Course(db.Model):
    """
    Course model
    """
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    code = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    assignments = db.relationship("Assignment", cascade = "delete", back_populates="course")
    instructors = db.relationship("User", secondary = "instructor_course", back_populates = "instructing_courses")
    students = db.relationship("User", secondary = "student_course", back_populates = "student_courses")


    def __init__(self, **kwargs):
        """
        Initialize course
        """

        self.code = kwargs.get("code")
        self.name = kwargs.get("name")

    def serialize(self):
        """
        Serialize a course object
        """
        return {
            "id":self.id,
            "code": self.code,
            "name": self.name,
            "assignments": [a.simple_serialize() for a in self.assignments],
            "instructors": [u.simple_serialize() for u in self.instructors],
            "students": [u.simple_serialize() for u in self.students]
        }
    
    def simple_serialize(self):
        """
        Serialize a course object without users (prevents infinite loop)
        """
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
        }
    
class User(db.Model):
    """
    User model
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable = False)
    netid = db.Column(db.String, nullable = False)
    instructing_courses = db.relationship("Course", secondary = "instructor_course", back_populates = "instructors")
    student_courses = db.relationship("Course", secondary = "student_course", back_populates = "students")
    submissions = db.relationship("Submission", cascade = "delete", back_populates = "user")

    def __init__(self, **kwargs):
        """
        Initialize an user object
        """
        self.name = kwargs.get("name")
        self.netid = kwargs.get("netid")

    def serialize(self):
        """
        Serialize an user object
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
            "courses": {
                "instructing_courses": [c.simple_serialize() for c in self.instructing_courses],
                "student_courses": [c.simple_serialize() for c in self.student_courses]
            },
            "submissions": [s.serialize() for s in self.submissions]
        }
    
    def simple_serialize(self):
        """
        Serialize an user object without courses
        """
        return {
            "id": self.id,
            "name": self.name,
            "netid": self.netid,
        }
    
class Assignment(db.Model):
    """
    Assignment mode
    """
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    title = db.Column(db.String, nullable = False)
    due_date = db.Column(db.Integer, nullable = False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable = False)
    course = db.relationship("Course", back_populates="assignments")
    submissions = db.relationship("Submission", back_populates = "assignment", cascade = "delete")

    def __init__(self, **kwargs):
        """
        Initialize an assignment object
        """
        self.title = kwargs.get("title")
        self.due_date = kwargs.get("due_date")
        self.course_id = kwargs.get("course_id")

    def serialize(self):
        """
        Serialize an assignment object
        """
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "course": [self.course.simple_serialize()],
            "submissions": [s.serialize() for s in self.submissions]
        }
    
    def simple_serialize(self):
        """
        Serialize an assignment object without course
        """
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "course_id": self.course_id,
            "submissions": [s.simple_serialize() for s in self.submissions]
        }
    
class Submission(db.Model):
    """
    Submission model
    """
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    content = db.Column(db.String, nullable = False)
    score = db.Column(db.Integer, nullable = True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignments.id"), nullable = False)
    assignment = db.relationship("Assignment", back_populates = "submissions")
    user = db.relationship("User", back_populates="submissions")

    def __init__(self, **kwargs):
        """
        Initializes a submission object
        """
        self.id = kwargs.get("id")
        self.user_id = kwargs.get("user_id")
        self.content = kwargs.get("content")
        self.score = kwargs.get("score")
        self.assignment_id = kwargs.get("assignment_id")

    def serialize(self):
        """
        Serializes a submission object
        """
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "user_id": self.user_id,
            "assignment": self.assignment.simple_serialize(),
            "user": self.user.simple_serialize()
        }
    
    def simple_serialize(self):
        """
        Simply serialize for course serialization
        """
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "user_id": self.user_id
        }

    