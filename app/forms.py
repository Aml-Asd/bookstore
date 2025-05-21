from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, FloatField, IntegerField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from bookstore_flask_project.app.models import User # For checking existing username/email during registration

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email address is already registered.')

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=140)])
    author = StringField('Author', validators=[Length(max=140)])
    isbn = StringField('ISBN', validators=[Length(max=20)]) # Add unique validator in route if needed
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0.01)])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    # For cover_image, Flask-WTF's FileField handles the <input type="file">.
    # Actual file saving logic will be in the route.
    cover_image = FileField('Cover Image') # Optional: add validators like FileAllowed from flask_wtf.file
    category = StringField('Category', validators=[Length(max=50)])
    publication_date = StringField('Publication Date (YYYY-MM-DD)', validators=[Length(max=10)]) # Or use DateField
    submit = SubmitField('Save Book')

class AddToCartForm(FlaskForm):
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired(), NumberRange(min=1, max=100)])
    submit = SubmitField('Add to Cart')

class UpdateCartItemForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0, max=100)]) # min=0 for removal
    submit = SubmitField('Update')