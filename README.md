# finance
Flask app to buy/sell imaginary stocks. Did this as part of [CS50 problem set 9](https://cs50.harvard.edu/x/2022/psets/9/finance/)

What I coded: 
1. **app.py -- register**. Lets user sign up on the site. Stores user info in a sqlite3 database
2. **app.py -- quote**. Lets user look up stock prices by inputting the stock symbol.
3. **app.py -- buy**. Lets user "purchase" stocks, updates the database with owned stocks and money balance.
4. **app.py -- index**. Shows a summary table of user owned stock and funds. 
5. **app.py -- sell**. Lets user sell stocks, removes sold stocks from user's owned stocks, updates money balance.
6. **app.py -- history**. Shows user's transaction history.
7. **all .html templates/** except apology.html, login.html, layout.html.

All other code was provided by CS50
