#! /usr/bin/bash

Right now pushing to the sever is not an easy feat, and there are a few issues I would like to address
First the all local changes are added to the git repo, then pushed to github,
please ensure that everything that needs to be hidden is not included in the git repo.
Once the push is done, remember to do one last validation of the website to ensure everything is working as expected.

Now for the hard bits:

1. Ensure you have SSH access to the server, and that your public key is added to the server's authorized_keys file.
2. Take down the website by running the following command on the server:
	(current implementation)
	```bash
		# we are in ssh session
		screen -l
		# find and connect to relevent screen session
		# then just press ctrl+c to stop the server
		git pull
		# then run the server when the pull is done
		./run_target.sh
	```
	(future implementation)
	```bash
		# we are in ssh session
		# stop the service using systemd
		sudo systemctl stop mywebsite.service
		git pull
		# then start the service again
		sudo systemctl start mywebsite.service
	```
3. Test to see that the site is up and running, if not, debug the issue.
4. Exit the ssh session and return to your local machine.
5. Check CDN and cache settings to ensure that the latest version of your site is being served,
   and clear caches if necessary.
6. Finally, validate the website to ensure everything is functioning as expected.

Some issues that need addresssing:
1. Updating the server should not erase the current game of wordgame, we have decided going forth that
	word game will be persistent always, and this should remain the case
2. static should no be a part of this repo, this should be managed seperately, and we can add a script
	to the repo to push to the static library on the server or pull from it, but it shouldnt be a part of the repo.