import os
from flask import Flask, redirect, render_template, request, session
from flask_mail import Mail, Message
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from cs50 import SQL
from help import login_required
from tempfile import mkdtemp


#config application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Config SQLite database
db = SQL("sqlite:///store.db")

#config to send emails
#app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
#app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
#app.config["MAIL_PORT"] = 587
#app.config["MAIL_SERVER"] = "smtp.gmail.com"
#app.config["MAIL_USE_TLS"] = True
#app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
#app.config['MAIL_USE_SSL'] = False

#mail = Mail(app)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response




@app.route('/')
def index():
    produ = db.execute("SELECT * FROM produtos ORDER BY about")
    return render_template("index.html",produ=produ, log=session.get("user_id"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        # Remember that user logged in
        if not request.form.get("username"):
            return render_template("error.html",problem="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html",problem="must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html",problem="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")
        # Redirect to another page
        return redirect('/')
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
@app.route("/register",methods=["GET","POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Making sure the user provid useful information
        if not request.form.get("username"):
            return render_template("error.html",problem="Must provide valid username")

        if not request.form.get("password"):
            return render_template("error.html",problem="Must provide valid password")

        if not request.form.get("passwordconf"):
            return render_template("error.html",problem="Must provide valid confirmation password")
        
        if not request.form.get("email"):
            return render_template("error.html",problem="Must provide valid email")

        if request.form.get("password")!=request.form.get("passwordconf"):
            return render_template("error.html",problem="The password and confirmation password must be iqual")

        if db.execute("SELECT * FROM users WHERE username = ?",request.form.get("username")) != []:
            return render_template("error.html",problem="Username already in use")
        
        if db.execute("SELECT * FROM users WHERE email = ?",request.form.get("email")) != []:
            return render_template("error.html",problem="Email already in use")
        else:
            db.execute("INSERT INTO users(username, hash, email) VALUES(?, ?, ?)",request.form.get("username"),generate_password_hash(request.form.get("password")), request.form.get("email"))
            #message = Message("You are registered!", recipients=[request.form.get("email")])
            #mail.send(message)
            return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "GET":
        user_id = session.get("user_id")
        produtos = db.execute("SELECT * FROM checkoutproduct WHERE user_id = ?", user_id)
        return render_template("cart.html", produtos=produtos)
    
    if request.method == "POST":
        user_id = session.get("user_id")
        id = request.form.get("id")
        quantity = request.form.get("quantity")
        if quantity != None:
            product = db.execute("SELECT * FROM produtos WHERE id = ?", id)
            db.execute("UPDATE checkoutproduct SET product_quantity = ? WHERE user_id = ? AND product_id = ?",quantity, user_id, id)
            db.execute("UPDATE checkoutproduct SET total_payment = ? WHERE product_quantity = ? AND user_id = ? AND product_id = ?", (float(quantity)*float(product[0]['price'])), quantity, user_id, id)
            return redirect("/cart")
        else:
            product = db.execute("SELECT * FROM produtos WHERE id = ?", id)
            db.execute("INSERT INTO checkoutproduct(user_id, product_id, product_name, product_price, total_payment) VALUES(?, ?, ?, ?, ?)", user_id, id, product[0]["name"], product[0]["price"], product[0]["price"])
            return redirect("/cart")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",problem=f"{e.name}, {e.code}")

# Listen for errors
#@for code in default_exceptions:

if __name__ == "__main__":
    app.run()
