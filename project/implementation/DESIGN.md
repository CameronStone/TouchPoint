Design Document:

In short, we created a Flask web application that relies heavily on querying in and out of our SQL database (database.db). In that database, we have tables for users and friends. A key element of the friends table is a column friend_id, which helps keep track of which user this inputted friend is assigned to.

Within our back-end Python code in application.py, we have a few important routes.

Login, logout and register are fairly self explainatory. We utilized the session_id to help keep track of which user was currently logged in.

The start route is step one of our user's experience. They are able to add friends and in doing so, refresh the table of friends that they see displayed on the screen (initial request is GET, but those refreshed tables come from the POST request).

The data route is simple. This is where the "TouchPoint magic" happens. Existing overlaps that a friend and user share cause the priority of the friend to decrease (twice as much by same college as it does for same extracurricular or concentration). We felt this took into consideration the huge impact going to the same school has on how often to friends regularly see eachother.

Lastly, the time route involves some creative math to convert a TouchPoint index where lower numbers represent higher priority to fraction whose numerator (found using the index) must be bigger in order to represent those of higher priority. These fractions (or ratios) were used to calculate the amount of time each friend should receive.

Many of our HTML pages extend a layout.html to help simplify style and keep it consistent. An example of one that does not is register.html, since we did not want hyperlinks to other pages to be available on the registration page. We utilized Jinja and Javascript to help the user have opportunities to interact with the client-facing side of the web application.

We tested our application to identify bugs and built in many checks to help ensure a smooth experience for the user. We hope you enjoy the power of TouchPoint!