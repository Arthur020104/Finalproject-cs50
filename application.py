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
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_PORT"] = 465
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/',methods=["GET","POST"])
def index():
    if request.method=="POST":
        search = f'%{request.form.get("search")}%'
        produ = db.execute("SELECT * FROM produtos WHERE name LIKE ? ORDER BY length(about) DESC",search )
        if produ == []:
            return render_template("error.html",problem="We don't have this product", log=session.get("user_id"))
        return render_template("index.html",produ=produ, log=session.get("user_id"))
    produ = db.execute("SELECT * FROM produtos ORDER BY length(about) DESC")
    return render_template("index.html",produ=produ, log=session.get("user_id"))

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        # Remember that user logged in
        if not request.form.get("username"):
            return render_template("error.html",problem="must provide username", log=session.get("user_id"))

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html",problem="must provide password", log=session.get("user_id"))

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("error.html",problem="invalid username and/or password", log=session.get("user_id"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")
        # Redirect to another page
        return redirect('/')
    else:
        return render_template("login.html", log=session.get("user_id"))

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
            return render_template("error.html",problem="Must provide valid username", log=session.get("user_id"))

        if not request.form.get("password"):
            return render_template("error.html",problem="Must provide valid password", log=session.get("user_id"))

        if not request.form.get("passwordconf"):
            return render_template("error.html",problem="Must provide valid confirmation password", log=session.get("user_id"))
        
        if not request.form.get("email"):
            return render_template("error.html",problem="Must provide valid email", log=session.get("user_id"))

        if request.form.get("password")!=request.form.get("passwordconf"):
            return render_template("error.html",problem="The password and confirmation password must be iqual", log=session.get("user_id"))

        if db.execute("SELECT * FROM users WHERE username = ?",request.form.get("username")) != []:
            return render_template("error.html",problem="Username already in use", log=session.get("user_id"))
        
        if db.execute("SELECT * FROM users WHERE email = ?",request.form.get("email")) != []:
            return render_template("error.html",problem="Email already in use", log=session.get("user_id"))
        else:
            db.execute("INSERT INTO users(username, hash, email) VALUES(?, ?, ?)",request.form.get("username"),generate_password_hash(request.form.get("password")), request.form.get("email"))
            message = Message("You are registered!", recipients=[request.form.get("email")])
            mail.send(message)
            return redirect("/login")
    else:
        return render_template("register.html", log=session.get("user_id"))


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "GET":
        user_id = session.get("user_id")
        produtos = db.execute("SELECT * FROM checkoutproduct WHERE user_id = ?", user_id)
        return render_template("cart.html", produtos=produtos, log=session.get("user_id"))
    
    if request.method == "POST":
        user_id = session.get("user_id")
        id = request.form.get("id")
        quantity = request.form.get("quantity")
        if quantity != None or db.execute("SELECT * FROM checkoutproduct WHERE user_id = ? AND product_id = ?",user_id, id) != []:
            product = db.execute("SELECT * FROM produtos WHERE id = ?", id)
            if quantity == '0':
                db.execute("DELETE FROM checkoutproduct WHERE user_id = ? AND product_id = ?", user_id, id)
                return redirect("/cart")
            if quantity == None:
                unupdate_product = db.execute("SELECT * FROM checkoutproduct WHERE user_id = ? AND product_id = ?",user_id, id)
                quantity = unupdate_product[0]['product_quantity']
                quantity = quantity+1
                db.execute("UPDATE checkoutproduct SET product_quantity = ? WHERE user_id = ? AND product_id = ?",quantity, user_id, id)
                db.execute("UPDATE checkoutproduct SET total_payment = ? WHERE product_quantity = ? AND user_id = ? AND product_id = ?", (float(quantity)*float(product[0]['price'])), quantity, user_id, id)
                return redirect("/cart")
            db.execute("UPDATE checkoutproduct SET product_quantity = ? WHERE user_id = ? AND product_id = ?",quantity, user_id, id)
            db.execute("UPDATE checkoutproduct SET total_payment = ? WHERE product_quantity = ? AND user_id = ? AND product_id = ?", (float(quantity)*float(product[0]['price'])), quantity, user_id, id)
            return redirect("/cart")
        else:
            product = db.execute("SELECT * FROM produtos WHERE id = ?", id)
            db.execute("INSERT INTO checkoutproduct(user_id, product_id, product_name, product_price, total_payment) VALUES(?, ?, ?, ?, ?)", user_id, id, product[0]["name"], product[0]["price"], product[0]["price"])
            return redirect("/cart")

@app.route("/product", methods=["GET", "POST"])
@login_required
def addproduct():
    if request.method == "GET":
        return render_template("productadd.html", log=session.get("user_id"))
        
    if request.method == "POST":
        name = request.form.get("product_name")
        about = request.form.get("about")
        image = request.form.get("img")
        price = request.form.get("price")
        db.execute("INSERT INTO produtos(name, about, picture, price) VALUES(?, ?, ?, ?)",name, about, image, price)
        email = db.execute('SELECT email FROM users WHERE id = ?',session.get("user_id"))
        message = Message(f"You just register a new product with the name:{name}", recipients=[email[0]['email']])
        mail.send(message)
        return redirect("/")

@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    if request.method == "GET":
        produtos = db.execute("SELECT * FROM checkoutproduct WHERE user_id=?",session.get("user_id"))
        return render_template("checkout.html",produtos=produtos)
    elif request.method == "POST":
        produtos = db.execute("SELECT * FROM checkoutproduct WHERE user_id=?",session.get("user_id"))
        db.execute("DELETE FROM checkoutproduct WHERE user_id=?",session.get("user_id"))
        email = db.execute('SELECT email FROM users WHERE id = ?',session.get("user_id"))
        message = f"You just bought {len(produtos)} products with the names"
        product_totalprice = 0
        for product in produtos:
            product_totalprice = product_totalprice+product["total_payment"]
            message =f"{message}, {product['product_name']}"
        message =f"{message}."
        mensagem  =Message(f"{message} The total price paid was ${product_totalprice}", recipients=[email[0]['email']])
        mail.send(mensagem)
        return render_template("checkout.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",problem=f"{e.name}, {e.code}", log=session.get("user_id"))


if __name__ == "__main__":
    app.run()
 #Listen for errors
#@for code in default_exceptions:
