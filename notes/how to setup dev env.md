The following env variables need to be added to the .env file in the root of the directory:

 - ENVIRONMENT_NAME=
 - CANON_DOMAIN=
 - SECRET_KEY=
 - ADMIN_PATH=
 - DBADDR=
 - cfSiteKey=
 - cfSecretKey=
 - mailServerKey=
 - loginAddress=
 - mailAddress=
 - googleclientid=
 - googleclientsecret=
 - spotifyAppId=
 - spotifyAppSecret=
 - WORD_DICTIONARY_PATH=

You need to create a new environment with python:
`python -m venv venv`
Then source the environment and install the requirements
`pip install -r requirements.txt`

You will need to create a new database with the schema from schema.py,
this is not a huge deal as long as the DBADDR is set to a valid db and the environement name is "development" just run:
`flask create_db`

I think that is everything for now?
