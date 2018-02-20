import pymysql, os, re, json
from flask import Flask, request, render_template, send_file, session, g, redirect, url_for

app = Flask(__name__)
conn = pymysql.connect(host='127.0.0.1', user='root', db='appsec')
a = conn.cursor()
app.secret_key = os.urandom(24)



@app.route('/', methods=['GET'])
def index():
    try:
        if session['user'] != None:
            user = session['user']
            sql1 = "SELECT address FROM images WHERE uploader = '" + user + "'"
        else:
            sql1 = "SELECT address FROM images"
    except:
        sql1 = "SELECT address FROM images"
    a.execute(sql1)
    data = a.fetchall()
    paths = []
    for i in data:
        i = str(i)
        m = re.search("'", i)
        start = m.start() + 1
        i = i[start:]
        m = re.search("'", i)
        end = m.end() - 1
        i = i[:end]
        paths.append(i)

        try:
            if session['user'] != None:
                testvar = session['user']
            else:
                testvar = "Nope"
        except:
            testvar = "Nope"
    #dict = json.dumps(dict)
    return (render_template('home.html', paths = paths, testvar = testvar))

app.config['UPLOAD_FOLDER'] = os.path.abspath('static/uploads')
@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if session['user'] != None:
            user = session['user']
        else:
            user = "all"
    except:
        user = "all"
    caption = request.form['caption']
    file = request.files['image']
    f = os.path.join(os.path.abspath('static/uploads'), file.filename)
    file.save(f)
    name = str(file.filename)
    path = "static/uploads/" + name
    sql = "INSERT INTO `images`(`name`, `caption`, `address`, `uploader`) VALUES ('" + name + "','" + caption + "','" + path + "','" + user + "')"
    a.execute(sql)
    conn.commit()
    return(redirect(url_for('index')))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user', None)
        cname = request.form['username']
        cpass = request.form['password']
        if len(cname) != 0 and len(cpass) != 0:
            sql = "SELECT `Username`, `Password` FROM `users` WHERE Username = '" + cname + "' and Password = '" + cpass + "'"
            a.execute(sql)
            data = a.fetchall()
            if len(data) != 0:
                session['user'] = request.form['username']
                return redirect(url_for('index'))
            else:
                status = 1
                return (render_template('login.html',status = status))
    else:
        return(render_template('login.html'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        usernm = request.form['user']
        passwd = request.form['pass']
        if len(usernm) != 0 and len(passwd) != 0:
            sql = "INSERT INTO `users`(`Username`, `Password`) VALUES ('" + usernm + "','" + passwd + "')"
            status = a.execute(sql)
            conn.commit()
            if status == 1:
                return(render_template('signup.html',status = status, usernm = usernm))
        else:
            status = 2
            return (render_template('signup.html',status = status))
    else:
        return(render_template('signup.html'))

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


if __name__ == "__main__":
    app.run(debug=True)