# Todo-app Web API
## created with Django REST framework
# Description
<br />
<p>
  Version 1 of a RESTFul API to create users and tasks for Todo Application. Users can register and keep track of tasks. Admin users can create, update, delete tasks and can also create staff users to check all the tasks.
</p>
<br />
# Auth System
<p>
  All the requests made to the API need an Authorization header with a valid token. In order to obtain a valid token it's necesary to send a request ```POST /api/auth/login/``` with username and password. To register a new user it's necesary to make a request `POST /auth/register/` with the params:<br />
</p>

