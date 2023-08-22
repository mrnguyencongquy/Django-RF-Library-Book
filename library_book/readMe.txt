
### install Library ###
* Create a virtual environment to isolate our package dependencies locally
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

* Install Django and Django REST framework into the virtual environment
pip install django
pip install djangorestframework

* Install a relational SQL: PostgreSQL
pip install psycopg2

* Install JTW and others by install requirements.txt
pip install -r requirements.txt

### config Settings.py ###
* Setup PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'library_book_db',
        'USER': 'postgres',
        'PASSWORD': 9,
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

https://www.django-rest-framework.org/


### DEBUG ###
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
        },
        {
            "name":"library_book",
            "python": "C:/Users/quy.nc.SUTRIXMEDIA1/Desktop/project/DE/python/django/DRF_1/venv/Scripts/python.exe",
            "type": "python",
            "request": "launch",
            "program": "C:/Users/quy.nc.SUTRIXMEDIA1/Desktop/project/DE/python/django/DRF_1/library_book/manage.py",
            "console": "integratedTerminal",
            "args": ["runserver"]
        }
    ]
}