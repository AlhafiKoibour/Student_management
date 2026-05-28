import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User, StudentProfile

# Fonction d'aide pour valider la force d'un mot de passe
def check_password_strength(password):
    """
    Vérifie si le mot de passe respecte la politique de sécurité :
    - Au moins 8 caractères
    - Au moins une majuscule
    - Au moins une minuscule
    - Au moins un chiffre
    - Au moins un caractère spécial (@$!%*?&_#...)
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[@$!%*?&_#\-+=§:]", password):
        return False
    return True


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Invalid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Invalid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError("This email address is already registered.")

    def validate_password(self, password):
        if not check_password_strength(password.data):
            raise ValidationError(
                "Password must be at least 8 characters long and include one uppercase letter, "
                "one lowercase letter, one number, and one special character (@$!%*?&_#...)."
            )


class ProfileCompletionForm(FlaskForm):
    matricule = StringField('Student Number', validators=[
        DataRequired(message="Student number is required."),
        Length(min=3, max=50, message="Student number must be between 3 and 50 characters.")
    ])
    nom = StringField('Last Name', validators=[
        DataRequired(message="Last name is required."),
        Length(min=2, max=100, message="Last name must be between 2 and 100 characters.")
    ])
    prenom = StringField('First Name', validators=[
        DataRequired(message="First name is required."),
        Length(min=2, max=100, message="First name must be between 2 and 100 characters.")
    ])
    filiere = StringField('Program', validators=[
        DataRequired(message="Program is required."),
        Length(min=2, max=100, message="Program must be between 2 and 100 characters.")
    ])
    est_boursier = RadioField('Scholarship Status', choices=[
        ('1', 'Scholarship'),
        ('0', 'No Scholarship')
    ], default='0', validators=[DataRequired(message="Please select a scholarship status.")])
    submit = SubmitField('Save Profile')

    def validate_matricule(self, matricule):
        profile = StudentProfile.query.filter_by(matricule=matricule.data.upper()).first()
        if profile:
            raise ValidationError("This student number is already in use.")


class AdminAddStudentForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Invalid email address.")
    ])
    password = PasswordField('Password (default)', validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    matricule = StringField('Student Number', validators=[
        DataRequired(message="Student number is required.")
    ])
    nom = StringField('Last Name', validators=[
        DataRequired(message="Last name is required."),
        Length(min=2, max=100, message="Last name must be between 2 and 100 characters.")
    ])
    prenom = StringField('First Name', validators=[
        DataRequired(message="First name is required."),
        Length(min=2, max=100, message="First name must be between 2 and 100 characters.")
    ])
    filiere = StringField('Program', validators=[
        DataRequired(message="Program is required.")
    ])
    est_boursier = RadioField('Scholarship Status', choices=[
        ('1', 'Scholarship'),
        ('0', 'No Scholarship')
    ], default='0', validators=[DataRequired(message="Please select a scholarship status.")])
    submit = SubmitField('Add Student')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError("This email address is already registered.")

    def validate_matricule(self, matricule):
        profile = StudentProfile.query.filter_by(matricule=matricule.data.upper()).first()
        if profile:
            raise ValidationError("This student number is already in use.")

    def validate_password(self, password):
        if not check_password_strength(password.data):
            raise ValidationError(
                "Password must be at least 8 characters long and include one uppercase letter, "
                "one lowercase letter, one number, and one special character."
            )


class AdminEditStudentForm(FlaskForm):
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Invalid email address.")
    ])
    matricule = StringField('Student Number', validators=[
        DataRequired(message="Student number is required.")
    ])
    nom = StringField('Last Name', validators=[
        DataRequired(message="Last name is required."),
        Length(min=2, max=100, message="Last name must be between 2 and 100 characters.")
    ])
    prenom = StringField('First Name', validators=[
        DataRequired(message="First name is required."),
        Length(min=2, max=100, message="First name must be between 2 and 100 characters.")
    ])
    filiere = StringField('Program', validators=[
        DataRequired(message="Program is required.")
    ])
    est_boursier = RadioField('Scholarship Status', choices=[
        ('1', 'Scholarship'),
        ('0', 'No Scholarship')
    ], default='0', validators=[DataRequired(message="Please select a scholarship status.")])
    is_active = RadioField('Account Status', choices=[
        ('1', 'Active'),
        ('0', 'Blocked')
    ], default='1', validators=[DataRequired(message="Please select the account status.")])
    submit = SubmitField('Save Changes')

    # user_id must be passed during initialization to exclude the current user
    def __init__(self, user_id=None, *args, **kwargs):
        super(AdminEditStudentForm, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_email(self, email):
        user = User.query.filter(User.email == email.data.lower(), User.id != self.user_id).first()
        if user:
            raise ValidationError("This email address is already registered to another account.")

    def validate_matricule(self, matricule):
        profile = StudentProfile.query.filter(StudentProfile.matricule == matricule.data.upper(), StudentProfile.user_id != self.user_id).first()
        if profile:
            raise ValidationError("This student number is already used by another student.")
