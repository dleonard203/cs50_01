# Welcome to Bookworm!

This is my CS50 Project 1 website, Bookworm. It was made with Flask, Jinja2, and CSS. Users are able to log in, read reviews,
submit reviews, and call the goodreads API through this website. On windows, if you run `$Env:FLASK_APP="application.py` while in the directory of cs50_01,
running `flask run` will start the web server on localhost port 5000. In a browser, you can then go to `http://localhost:500` to get
to the landing page. To start leaving reviews, register for an account and sign in!

## Files

application.py is where the flask app lives. All routing, as well as some helper functions, live here.

import.py is how books.csv gets inserted into the 'books' PostgreSQL table that supports this project.

/templates folder contains all Jinja2 templates that are used throughout the app.

/static/css contains the two CSS files used for styling the website

/static/images contains the Bookworm logo
