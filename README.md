# AnimAuth
[![license | AGPLv3](https://img.shields.io/badge/license-AGPLv3-blue)](https://www.gnu.org/licenses/agpl-3.0.html)
[![part of | authly](https://img.shields.io/badge/part_of-authly-%23f1c40f)](https://authly.hackclub.com)
![hackatime status](https://hackatime-badge.hackclub.com/U091HKKKJRH/AuthlyProject)

This is an image hosting/sharing site that utilises GIFs 
instead of passwords when logging in.

## How does it work?
### Authentication
Instead of entering a password when registering/logging in,
the user is prompted to instead draw 3-10 frames and choose
the animation speed per frame of a 10x10px GIF image. 
Internally, the server reads the frames as separate PNG images, 
and concatenates the animation speed to generate a "password".

### Actual site functionally
Nothing special here, just the standard uploading/downloading,
and the user can also add a title and description
(with limits.)

## Setup (for testing)
DO NOT follow these steps if you want to host 
AnimAuth in a production environment.

If you don't know what a production environment is, then 
you can probably proceed.
### Prerequisites:
```
python >= 3.10
blinker==1.9.0
click==8.2.1
filetype==1.2.0
Flask==3.1.1
Flask-SQLAlchemy==3.1.1
Flask-UUID==0.2
flask_session_captcha==1.5.0
greenlet==3.2.4
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
pillow==11.3.0
python-dotenv==1.1.1
SQLAlchemy==2.0.43
typing_extensions==4.14.1
Werkzeug==3.1.3
```
### Steps
(Do not include the "$" when copying commands.)
#### 1. Clone the repository and change directory:
```shell
$ git clone https://github.com/x-9917638/AnimAuth.git
$ cd AnimAuth
```
#### 2. Create a virtual environment (optional)
```shell
$ python -m venv .venv
```
Activate the environment (MacOS/Linux)
```shell
$ source .venv/bin/activate
```
Activate the environment (Windows)
```shell
$ ./.venv/scripts/activate.bat
```
#### 3. Install requirements
```shell
$ pip install -r requirements.txt
```
#### 4. Create a secret key
```shell
$ python -c "from base64 import b64encode; from os import urandom; print(b64encode(urandom(512)).decode('utf-8'))" > ./.env
```
#### 5. Run the development server
```shell
$ flask run 
```
or 
```shell
$ python app.py
```
