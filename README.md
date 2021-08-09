# ChatRoom


#### Video Demo:
https://drive.google.com/file/d/1GOtBckNt41rJBW-kotceeWntlDZLQmYc/view


#### Description:
This is a chat room application where users need to register in order to be able to log in.
Then they can chat with one another within one room. The main reason for creating this
application is to create something similar to other social media chat applications but
with its own unique features. This is a perfect application that can be set up within the same
household to communicate with one another across rooms because there is only one room and
multiple users can join to this room.

The positive of this application is that users can see who joined the room and who left.
On top of all this, messages only stored while there are users online. So once every users
has left the room, all messages are deleted. They are also deleted on server start, just to
make sure no previous conversations are stored.

The application uses an SQL database with sqlite3. Here there are three tables that are used
throughout the application. These are the following:
- users
    - id
    - display name
    - username
    - hash
- messages
    - display name
    - messages
    - date
- online users
    - display name

Throughout the application, the forms, buttons and links are interactive. Thus, creating
pleasant and friendly experience for the users. The design of this application
is very minimalistic and easy to read for the eye, as well as having a light and dark
mode so that user's can adjust the theme to their environment. For example, poeple may want
to use the Dark mode later at night while using the Light mode during the day.

The application.py contains all the backend code neccessary to serve the static files and
for API messages back and forth between the frontend and backend. In the backend, all
the data is stored within the chatapp.db, which is an SQL database that is accessed and
edited with queries. To ensure that there are no errors made when accessing and editing the
database, locks are used to ensure only one user can edit one table at a time.

The index.html file is the main page where users are able to talk to one another, and this
file uses the stylings from styles_home.css. This file constantly sends an API message to
the backend to request the messages, and this is how the messages are constantly updated.

The login.html file is for the login page while register.html is for the register page, and
both of these files use the styling from styles.css. Both of these files use API communication
with the backend.


### To run the application:
export FLASK_APP=application.py; flask run