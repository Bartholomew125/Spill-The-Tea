from wtforms import BooleanField, Form, SearchField, SelectField, StringField
from wtforms.validators import InputRequired

# https://stackoverflow.com/questions/58105688/how-to-put-description-of-the-field-in-the-form-field
class Search(Form):
    search_bar = SearchField(render_kw={"placeholder": "Search"}, 
        validators=[InputRequired("A search query is required to search")]
    )
    type_toggle = SelectField(choices=[("posts", "Posts"), ("users", "Users")])
