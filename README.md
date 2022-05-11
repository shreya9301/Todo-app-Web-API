# Todo-app Web API
### <b>created with Django REST framework</b>
<br>

# Description
<br />
<p>
  Version 1 of a RESTFul API to create users and tasks for Todo Application. Users who are athenticated into the system can register and keep track of tasks. Admin users can create, update, delete tasks and can also create staff users to check all the tasks.
</p>

# Auth System
<p>
  All the requests made to the API need an Authorization header with a valid token. In order to obtain a valid token it's necesary to send a request <code>POST /api/auth/login</code> with username and password. To register a new user it's necesary to make a request <code>POST /auth/register/</code> with the params:
  <code>
  {<br>
    'username',<br>
    'password', <br>
    'password2', <br>
    'email', <br>
    'first_name',<br>
    'last_name'<br>
  }
</code>
</p>

# End Points
## Auth
* <code>POST /auth/register/</code> - user register
* <code>POST /auth/login/</code> - user login (JWT access token is generated)
* <code>POST /auth/login/refresh/</code> - obtain another JWT token once access token expires

## Todo
* <code>GET /api/</code> - api overview
* <code>GET /api/getall</code> - get all todo items
* <code>GET /api/get/{id}/</code> - get single todo item
* <code>POST /api/create/{id}/</code> - create a new todo item
* <code>PUT /api/put/{id}/</code> - update single todo item
* <code>DELETE /api/delete/{id}/</code> - Delete a todo item

# Installation Process
### Install System Dependencies
* git
* pip

### Get the code
* Clone the repository in your terminal <code>git clone https://github.com/spantons/todo_app.git</code>

### Setup Virtual environment
* Create a virtual environtment - <code>virtualenv env</code>
* Activate VirtualENV - ubuntu : <code>source env/bin/activate</code> || windows : <code>\env\Scripts\activate</code>
* <code>cd todo_app</code>

### Install the project dependencies
```python
pip install -r requirements.txt
```
### Run the command to generate the database
```python
python manage.py makemigrations
python manage.py migrate
```

### Generate super user
```python
python manage.py createsuperuser
```

### Run the local server
<code>python manage.py runserver</code> - the application will be running on port 8000 http://127.0.0.1:8000/

