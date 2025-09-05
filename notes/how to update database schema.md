Right now in my main dev env I am using a sqlite db,
but on the server I am using mysql, so updating the schema on the server is done manually.
I do the updates via the CLI directly on the server(yes i know this is not ideal).

This does mean however that I need to be exact with my schema updates, as sqlite and mysql
have different syntax for some things.

The flask sqlalchemy class templates for the schema dont usually need to be adjusted for these syntax
differences, but if they do i try to write the code in a way that works for both.

When I do a schema update I do the following:
 - Make the updates to the schema.py file
 - Make the updates to the local sqlite db via either manually through the sqlite extension for vscode 
   or via a quick python script that uses the sqlalchemy classes to make the changes.
 - Validate the changes locally
 - Write a migration script in sqlite syntax to replicate the changes on the sever, sometimes this is
   just a few lines of sql, sometimes we need a full migration script, i usually just do this one table at a time
 - Take down webserver for migration (time frame for this does not matter as no one uses the site lol)
 - Run the migration script on the mysql db via the mysql CLI
 - Bring the webserver back up
 - Validate the changes on the live site
 - Celebrate that it worked or perhaps cry a little if it didnt

This is obviously not ideal, but it works for now.
