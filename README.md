# smule-analytics
I started this project with the intention to fetch my Smule data and store it in a local DB for doing analytics such as who are the people with whom I have performed the most number of duets, which of my songs have the most Loves, where are the people I have performed with located, etc.  I do still plan to implement these features, but I started out with a feature I wish existed in the Smule site, which is to list my (or any user's) performances in a simple format that allows me to listen to them and download them.

I developed the project in a pipenv Python 3.7 environment with Flask.  The backend DB is a PostgreSQL database running in a Docker container I downloaded from Docker Hub.  Below are the instructions for setting up the dev environment.  In the future, I will look into packaging the code in an easier to install package, but that is a lower priority.


