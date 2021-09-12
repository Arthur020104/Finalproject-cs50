from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import HTTPException, InternalServerError
from cs50 import SQL
from help import login_required

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db = SQL("sqlite:///store.db")
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
        if check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html",problem="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

        session["password"] = generate_password_hash(request.form.get("password"))
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
            return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if "cart" not in session:
        session["cart"] = []

    if request.method == "POST":
        id = request.form.get("id")
        if id:
            session["cart"].append(id)
        return redirect("/cart")
    
    produtos = db.execute("SELECT * FROM produtos WHERE id IN (?)", session["cart"])
    return render_template("cart.html", produtos=produtos)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",problem=f"{e.name}, {e.code}")


if __name__ == "__main__":
    app.run()
