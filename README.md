# Project

## Setup
```
Create python environment
python -m venv .adt-project

Activate environment
source .adt-project/bin/activate
```

## Development
```
flask run --debug -p 5000
.adt-project/bin/flask run --debug -p 5000
```

```
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

with app.app_context():
    db.Model.metadata.reflect(db.engine)

from models import *

@app.route("/")
def hello_world():
    # Database
    records = StoreDetails.query.all()
    print(records)
    return render_template('index.html')
```

## References

- https://github.com/maxcountryman/flask-login