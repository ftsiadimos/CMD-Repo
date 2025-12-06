from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class CommandForm(FlaskForm):
    command = StringField("Shell Command", validators=[DataRequired()])
    description = TextAreaField("Description (optional)")
    tags = StringField("Tags (comma‑separated)")
    submit = SubmitField("Save")