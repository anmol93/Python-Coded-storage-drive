import pymysql, os, re, hashlib
from flask import Flask, request, render_template, send_file, session, g, redirect, url_for
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length, AnyOf

#using Python framework flask to create a web server.
app = Flask(__name__)
conn = pymysql.connect(host='127.0.0.1', user='root', db='appsec')
a = conn.cursor()
app.secret_key = os.urandom(24)


app.config['SECRET_KEY'] = 'donotmesswithmeever'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LcbAEwUAAAAAMfPaorfowsOQP8MDUM-s0y517HM'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LcbAEwUAAAAAEmKWwtj2jjkxJfEvZcRnP6E1xun'
#app.config['TESTING'] = True

class LoginForm(FlaskForm):
    #username = StringField('username', validators=[InputRequired('A username is required!'), Length(min=5, max=10, message='Must be between 5 and 10 characters.')])
    #password = PasswordField('password', validators=[InputRequired('Password is required!'), AnyOf(values=['password', 'secret'])])
    recaptcha = RecaptchaField()


def cleaner(string):
    for i in string:
        ascii = ord(i)
        if ascii not in range(64,91) and ascii != 32 and ascii not in range(48,58) and ascii not in range(97,123):
            string = string.replace(i, " ")
    return(string)
#created a connection 'conn' to connect to the SQL database running through XAMPP on localhost.
#No password assigned currently to make the app deliberately vulnerable.

#home page is defined through a method callod index which only takes get requests.
@app.route('/', methods=['GET'])
def index():
    form = LoginForm()
    try:
        if session['user'] != None:
            user = session['user']
            sql1 = "SELECT address FROM images WHERE uploader = '" + user + "'"
            sql2 = "SELECT name FROM images WHERE uploader = '" + user + "'"
        else:
            sql1 = "SELECT address FROM images"
            sql2 = "SELECT name FROM images"
    except:
        sql1 = "SELECT address FROM images"
        sql2 = "SELECT name FROM images"
#if the user is in session, i.e logged in, the query uses the name of the uploader to search the database
# if no user is in session, all contents from the database are fetched
    a.execute(sql1)
    data = a.fetchall()
    paths = []

#The query saved in sql1 is executed, data is stored in the list paths which is then processed through the loop.
    for i in data:
        i = str(i)
        m = re.search("'", i)
        start = m.start() + 1
        i = i[start:]
        m = re.search("'", i)
        end = m.end() - 1
        i = i[:end]
        paths.append(i)
    paths.reverse()
    print(paths)
    a.execute(sql2)
    data1 = a.fetchall()
    imgnames = []

    for i in data1:
        i = str(i)
        m = re.search("'", i)
        start = m.start() + 1
        i = i[start:]
        m = re.search("'", i)
        end = m.end() - 1
        i = i[:end]
        imgnames.append(i)
    imgnames.reverse()
#The paths list contains the addresses to the images in the storage.
#The list is reversed to make the output chronological.
#Username is passed through the variable "testvar"
    try:
        if session['user'] != None:
            testvar = session['user']
        else:
            testvar = "Nope"
    except:
        testvar = "Nope"
    return (render_template('home.html', paths = paths, testvar = testvar,form = form ,imgnames = imgnames))
#The page is returned to be displayed, with the list 'paths' and 'testvar'


#Next function is used for uploading files which only accepts post requests
app.config['UPLOAD_FOLDER'] = os.path.abspath('static/uploads')
@app.route('/upload', methods=['POST'])
def upload_file():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            if session['user'] != None:
                user = session['user']
            else:
                user = "all"
        except:
            user = "all"
        caption = cleaner(request.form['caption'])
        file = request.files['image']
        f = os.path.join(os.path.abspath('static/uploads'), file.filename)
        file.save(f)
        name = str(file.filename)
        path = "static/uploads/" + name
        sql = "INSERT INTO `images`(`name`, `caption`, `address`, `uploader`) VALUES ('" + name + "','" + caption + "','" + path + "','" + user + "')"
        a.execute(sql)
        conn.commit()
        status = 1
    else:
        status = 2
    return redirect(url_for('index', form=form, status=status))
#If user was in session, the username is recorded and saved in the database, else not.


#The login method takes both username and passwords from the login page
#Checks to see if the entries match and grants access
#If error occurs while logging in, message is passed through variable called "Status".
@app.route('/login', methods=['GET', 'POST'])
def login():
    form2 = LoginForm()
    if request.method == 'POST':
        if form2.validate_on_submit():
            session.pop('user', None)
            cname = cleaner(request.form['username'])
            cpass = cleaner(request.form['password'])
            sql = "SELECT salt FROM `users` WHERE Username = '" + cname + "'"
            a.execute(sql)
            usersalt = str(a.fetchone())[1]
            cpass = cpass + usersalt
            cpass = cpass.encode("utf-8")
            cpasshash = (hashlib.sha1(cpass)).hexdigest()
            if len(cname) != 0 and len(cpasshash) != 0:
                sql = "SELECT `Username`, `Passwordhash` FROM `users` WHERE Username = '" + cname + "' and Passwordhash = '" + cpasshash + "'"
                a.execute(sql)
                data = a.fetchall()
                if len(data) != 0:
                    session['user'] = request.form['username']
                    return redirect(url_for('index'))
                else:
                    status = 1
                    return (render_template('login.html',status = status, form2=form2))
        else:
            return (render_template('login.html', form2=form2))
    else:
        return(render_template('login.html', form2=form2))

#The logout method would just pop the user out of the session.
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

#Delete method would only be accessible if the user is logged in.
#The user can only view and delete items that he/she uploaded, while they are logged in.
@app.route('/delete', methods=['POST'])
def delete():
    if request.method == 'POST':
        if session['user'] != None:
            delete_var = request.form['delete_act']
            sql2 = "DELETE FROM `images` WHERE address='" + delete_var + "' LIMIT 1;"
            a.execute(sql2)
            conn.commit()
            return redirect(url_for('index'))
    else:
        return("Not allowed")

#The signup page just creates a username and password pair and passes them to the database, if they're valid.
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form1 = LoginForm()
    if request.method == 'POST':
        if form1.validate_on_submit():
            usernm = cleaner(request.form['user'])
            passwd = cleaner(request.form['pass'])
            if len(usernm) != 0 and len(passwd) != 0:
                sql = "SELECT MAX(salt) FROM users"
                a.execute(sql)
                maxsalt = str(a.fetchone())
                maxsalt = int(maxsalt[1])
                newsalt = maxsalt + 1
                passwd = passwd + str(newsalt)
                passwd = passwd.encode("utf-8")
                passhash = (hashlib.sha1(passwd)).hexdigest()
                sql = "INSERT INTO `users`(`Username`, `Passwordhash`, `salt`) VALUES ('" + usernm + "','" + passhash + "','" + str(newsalt) + "')"
                status = a.execute(sql)
                conn.commit()
                if status == 1:
                    return(render_template('signup.html',status = status, usernm = usernm, form1 = form1))
            else:
                status = 2
                return (render_template('signup.html',status = status, form1 = form1))
        else:
            status = 3
            return (render_template('signup.html', status=status, form1=form1))
    else:
        return(render_template('signup.html', form1 = form1))
#The following methods implement the sessions module
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

@app.route('/getsession')
def getsession():
    if 'user' in session:
        return session['user']

    return 'Not logged in!'

@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return 'Dropped!'


@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        return("post")
    else:
        return(send_file("static/uploads/apple.png", mimetype='image/png'))

@app.route('/form1', methods=['GET', 'POST'])
def form1():
    form2 = LoginForm()

    if form2.validate_on_submit():
        return "Bitch"
    return render_template('form.html', form2=form2)
if __name__ == "__main__":
    app.run(debug=True)
