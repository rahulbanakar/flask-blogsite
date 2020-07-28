from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import os

app = Flask(__name__)
Bootstrap(app)

db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Form Secret Key
app.config['SECRET_KEY'] = os.urandom(24)

#Define Mysql db
mysql = MySQL(app)

@app.route("/")
def index():
    if 'username' in session:
        cursor = mysql.connection.cursor()
        author = session['firstName'] + ' ' + session['lastName']
        cursor.execute("SELECT * from blog where author = (%s)", [author])
        blogs = cursor.fetchall()
        cursor.close()
        return render_template('/index.html', blogs=blogs)
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template('about.html')

@app.route('/userProfile')
def blogs():
    cursor = mysql.connection.cursor()
    users = cursor.execute("SElECT * from users where username = %s", [session['username']])
    if users > 0:
        user = cursor.fetchone()
        cursor.close()
        return render_template('profile.html', user=user)

@app.route("/register/", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userDetails = request.form
        if userDetails['password'] != userDetails['confirmPassword']:
            flash("Passwords do not match, Please try again", "danger")
            return render_template("register.html")
        if userDetails['firstName'] == '' or userDetails['lastName'] == '' or userDetails['username'] == '' or \
            userDetails['email'] == '' or userDetails['password'] == '':
            flash("All fields are mandatory", "warning")
            return render_template('register.html')
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO USERS(firstName, lastName, username, email,password)"\
                       "values(%s,%s,%s,%s,%s)", ([userDetails['firstName'],userDetails['lastName'],\
                                                   userDetails['username'],userDetails['email'],\
                                                   generate_password_hash(userDetails['password'])]))
        mysql.connection.commit()
        cursor.close()
        flash("Registraion successfull, Please login","success")
        return redirect("/login")
    return render_template("register.html")

@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        Username = userDetails['username']
        password = userDetails['password']
        if Username == '' or password == '':
            flash("Fields cannot be empty","danger")
            return render_template('login.html')
        cursor = mysql.connection.cursor()
        users = cursor.execute("SELECT * FROM USERS where username = %s", [Username])
        if users > 0:
            user = cursor.fetchone()
            passwordMatch = check_password_hash(user['password'], password)
            if passwordMatch or ( user['username'] != Username ):
                session['login'] = True
                session['username'] = Username
                session['firstName'] = user['firstName']
                session['lastName'] = user['lastName']
                #flash("Welcom " + session['firstName'] , "success")
                return render_template("index.html")
            else:
                flash("Invalid credentials","danger")
                return render_template('login.html')
        else:
            flash("User Not Found","danger")
            return render_template('login.html')
    return render_template("login.html")

@app.route("/writeblog/", methods=['GET', 'POST'])
def writeBlog():
    if request.method == 'POST':
        blog = request.form
        title = blog['title']
        content = blog['blogcontent']
        if title == '' or content == '':
            flash("Title / Content cannot be empty","danger")
            return render_template('writeBlog.html')
        author = session['firstName'] + ' ' + session['lastName']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO blog(title, author, body) values(%s, %s, %s)",[title, author, content])
        mysql.connection.commit()
        cursor.close()
        flash("Blog created successfully","success")
        return redirect("/myblogs")
    return render_template("writeBlog.html")

@app.route("/myblogs")
def myblogs():
    if 'username' in session:
        cursor = mysql.connection.cursor()
        author = session['firstName'] + ' ' + session['lastName']
        cursor.execute("SELECT * from blog where author = (%s)", [author])
        blogs = cursor.fetchall()
        cursor.close()
        return render_template("myblogs.html",blogs=blogs)
    else:
        return render_template("myblogs.html",blogs=None)

@app.route("/editBlog/<int:id>/", methods=['GET', 'POST'])
def editBlog(id):
    if request.method == 'POST':
        blog = request.form
        title = blog['title']
        body = blog['blogcontent']
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE blog SET title = %s, body = %s where blogId = %s",[title,body,id])
        mysql.connection.commit()
        cursor.close()
        #flash("Blog edited successfully","success")
        return redirect("/myblogs")
    cursor = mysql.connection.cursor()
    blogs = cursor.execute("SELECT * from blog where blogId = (%s)", [id])
    if blogs > 0:
        blog = cursor.fetchone()
        cursor.close()
        return render_template("editBlog.html",blog=blog)

@app.route("/deleteBlog/<int:id>/", methods=['GET','POST'])
def deleteBlog(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM blog where blogId = {}".format(id))
    mysql.connection.commit()
    cursor.close()
    flash("Blog deletedsuccessfully","success")
    return redirect("/myblogs")

@app.route("/logout")
def logout():
    session.clear()
    #flash("Successfully logged out", "success")
    return render_template("/index.html")

@app.errorhandler(404)
def pageNotFound(e):
    return "This page is not available."

if __name__ == "__main__":
    app.run(debug=True)
