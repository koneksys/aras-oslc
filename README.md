# ARAS   OSLC API

Implementation of an OSLC API to work with Aras

This OSLC API will manage the ItemTypes defined from an
administrator to be exposed as a ServiceProvider and
to be able to consume the queryCapability to retrieve 
the information in its RDF representation.

### Getting the code ###

To get the code of this project for testing or installing it,
it is required to use some git commands for it.

```bash
git clone git@github.com:koneksys/aras-oslc.git
```

This command will create a folder called `aras-oslc`
within your folder location.

### Compiling the code

For generating/installing the required environment and dependencies for running
the application, it is required to execute some prior steps.

> Note: The project uses Makefile to generate this elements, make sure that the
> necessary packages are installed.  

There are different sections within the Makefile, the easiest way to install
all the elements required for the execution of the project is making all the 
components:

```bash
make all
```

This will create the virtual environment and will install all the dependencies
for the execution of the project.

There are other steps that could be find in the `Makefile` for executing
specific actions. 

### Installing the application ###

To install the application it is necessary to go into the 
`aras-oslc-api` folder and run the follow command:

```bash
pip install [-e] .
```

Remember, the `-e` parameter is for telling to the installer
that it is possible to edit the installation, this is
useful when it will be for a developing environment.

The previous command will install the application within
your environment.

### Executing the application ###

Once the application has been installed in the environment,
it is possible to execute it.

For doing this, it should be invoked by the follow command.

```bash
python -m aras_oslc_api
 * Serving Flask app "oslc_api.api" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

The previous command is running under a development stage.

# Using ARAS OSLC API

After the installation and the execution of the OSLC API, it is possible
to start using it to retrieve information from an ARAS API.

The usage of the ARAS OSLC API could be by adding it into an application or
by sending requests by the CLI (This two options will be described in this document)

## Authentication.

Since ARAS OSLC API it is an adapter to interact with an ARAS API for getting
the information on the RDF representation, it is necessary to have a pair of username
and password of the ARAS API application to authenticate with and to be able to get the data.

In ARAS OSLC API there are two endpoints that should be used for logging in and logout on
ARAS API.

### Login.

For logging in on ARAS OSLC API, it is required to use the credentials that should
be used for authenticating on ARAS API, it is required to send a `POST` request against 
the login endpoint of ARAS OSLC API, the credentials should be sent as an encoded form,
and particularly the password must be hashed before to be sent.

Here is an example using `cURL`:
 
```bash
password=$(md5 -qs "mypass")

curl -X POST "http://127.0.0.1:5000/api/oauth/login" \
     -H "accept: application/json" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=fabio.ribeiro&password=${password}"
     
{
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGQkU1RkE1Q...-0HORkyrATXTpkQ2iRw3vz7v4idlKEFX48pgzxrGUsC7Wpkw",
  "expires_in": 3600,
  "scope": "Innovator",
  "token_type": "Bearer"
}
```

Here is an example using `requests` from python.

```python
import requests
import hashlib

url = 'http://127.0.0.1:5000/api/oauth/login'
username = 'fabio.ribeiro'
password = hashlib.md5("mypass".encode('utf8')).hexdigest(),

payload = {
    'username': username,
    'password': password
}

response = requests.post(url, data=payload)
```

When printing the response from the json 

```python
response.json()
```

The response from ARAS API.
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGQkU1RkE1Q...-0HORkyrATXTpkQ2iRw3vz7v4idlKEFX48pgzxrGUsC7Wpkw",
  "expires_in": 3600,
  "scope": "Innovator",
  "token_type": "Bearer"
}
```

#### Describing the Response

As shown in both examples, the response contains a set of values in `JSON` format,
each pair of value in the response represents a specific parameter that describe the
authorization for the user.

##### access_token

The main value in the response is the `access_token`, that represents the 
authorized key that ARAS API has assigned to the user and that ARAS OSLC API
must use for the next requests when the user wants to access a resource.

##### expires_in

This value represents the time that the server can wait from the latest requests
until the new one, it is represented in seconds, using the value in the example, 
this means that after the last requests it will wait 60 min to take the `access_token`
as valid, one second after this, the token will expire, and the user must log in 
once again.

##### scopes

The scopes define the sections or features in which the server will allow 
the user to access, these scopes are defined in the ARAS API and the value
in the response will only describe the features available.

##### token_type

This value represents in which kind of Authorization header the `access_token`
must be used, for the case of ARAS OSLC API and ARAS API, the `access_token`
must be used as a `Bearer`

Something like:

```
Header: Authorization Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGQkU1RkE1Q...-0HORkyrATXTpkQ2iRw3vz7v4idlKEFX48pgzxrGUsC7Wpkw
```

This value will be used automatically by the ARAS OSLC API and it will be sent
as required by ARAS API.

### Requests using Token

Once the user has been authenticated and received the response with the 
`access_token` and the other values, it is possible to interact with 
ARAS OSLC API to retrieve information from ARAS API in the RDF representation.

After the authentication, for each request to the other endpoints of the
ARAS OSLC API, the API will require the `access_token` to validate
that the user is a valid user on ARAS API, for doing this, the ARAS OSLC API
will redirect the `access_token` to ARAS API validate the authenticity 
of the user.

To accomplish this, the requests must include a `header` on the requests,
and the `header` must be sent like this:

For cURL:

```bash
curl -X GET "http://127.0.0.1:5000/api/oslc" \
     -H "X-ARAS-ACCESS-TOKEN: eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGQkU1RkE1Q...-0HORkyrATXTpkQ2iRw3vz7v4idlKEFX48pgzxrGUsC7Wpkw"
```

For Python:

```python
import requests


url = 'http://127.0.0.1:5000/api/oslc'

headers = {
    'Accept': 'application/rdf+xml',
    'X-ARAS-ACCESS-TOKEN': 'eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGQkU1RkE1Q...-0HORkyrATXTpkQ2iRw3vz7v4idlKEFX48pgzxrGUsC7Wpkw',
}

response = requests.get(url, headers=headers)
```

The name of the header must be `X-ARAS-ACCESS-TOKEN`, this header will be
taken from ARAS OSLC API to generate the parameters to request from ARAS API.


### Logout.

To close the session on ARAS OSLC API and ARAS API and to destroy the value
for the `access_token`, it is required to send a `GET` request to the logout
endpoint on ARAS OSLC API.

As mentioned previously, this request must include the `access_token` as a header.


```bash
curl -X GET "http://127.0.0.1:5000/api/oauth/logout" \
     -H "accept: application/json" \
     -H "X-ARAS-ACCESS-TOKEN: eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGQkU1RkE1Q...-0HORkyrATXTpkQ2iRw3vz7v4idlKEFX48pgzxrGUsC7Wpkw"

{
  "message": "Session ended"
}

```


### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
