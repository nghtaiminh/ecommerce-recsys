# BookRec - Web Prototype

A web prototype to demonstrate session-based recommendation using 2 Transformer-based model which are SASRec and BERT4Rec

## Installation

### Setup Python environment

```bash
pip -m 
pip install -r requirements.txt
```

### Setup Database

Change the database connection string in `config.py` file. The data file is placed in `data` folder. After running the server the first time, the data file will be loaded in the database.
```
SQLALCHEMY_DATABASE_URI = "postgresql://<username>:<password>@<host>:<port>/<dbname>"
```

### Setup Models

Change the models' parameters (if the models are trained with different parameters) in `app/sasrec/__init__.py` and `app/bert4rec/__init__.py`. The weight files and map ID files are located at `app/sasrec` and `app/bert4rec`

### Run server locally

```bash
python index.py
```

The server is run on http://127.0.0.1:5000

username: user1(2, 3, 4, ...) ,password: 123456