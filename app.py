from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import random

app = Flask(__name__)
questions = []
app.secret_key = 'secret123'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'akshatanbaligar0126@gmail.com'
app.config['MAIL_PASSWORD'] = 'vujbpiszebxdoqaf'

mail = Mail(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    verified = db.Column(db.Boolean, default=False)


@app.route('/')
def home():
    return render_template('home.html')

from werkzeug.security import generate_password_hash
import random

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        otp = str(random.randint(100000, 999999))

        session['email'] = email
        session['password'] = hashed_password
        session['otp'] = otp

        msg = Message(
            'OTP Verification',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )

        msg.body = f'Your OTP is: {otp}'

        mail.send(msg)

        print("OTP sent to email:", email)

        return redirect(url_for('verify'))

    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if entered_otp == session.get('otp'):

            new_user = User(
                email=session.get('email'),
                password=session.get('password'),
                verified=True
            )

            db.session.add(new_user)
            db.session.commit()

            # 🔐 Log user in automatically
            session['user'] = session.get('email')

            # 🚀 Redirect to quiz
            return redirect(url_for('quiz'))

        return "Invalid OTP"

    return render_template('verify.html')
    return render_template('verify.html')

from werkzeug.security import check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.verified and check_password_hash(user.password, password):
            session['user'] = email
            return redirect(url_for('home'))

        return "Invalid credentials"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin123':
            otp = str(random.randint(100000, 999999))

            session['admin_otp'] = otp
            session['admin_user'] = username

            print("ADMIN OTP:", otp)

            msg = Message(
                'Admin OTP Verification',
                sender=app.config['MAIL_USERNAME'],
                recipients=['akshatanbaligar0126@gmail.com']
            )

            msg.body = f'Your Admin OTP is: {otp}'

            mail.send(msg)

            return redirect(url_for('admin_verify'))

        return "Invalid credentials"

    return render_template('admin_login.html')

@app.route('/admin_verify', methods=['GET', 'POST'])
def admin_verify():
    if request.method == 'POST':
        otp = request.form['otp']

        if otp == session.get('admin_otp'):
            session['admin'] = True
            session.pop('admin_otp', None)

            return redirect(url_for('admin'))

        return " Invalid OTP"

    return render_template('admin_verify.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        question = request.form.get('question')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        answer = request.form.get('answer')

        print("DEBUG:", question) 

        questions.append({
            'question': question,
            'options': [option1, option2, option3, option4],
            'answer': answer
        })

    return render_template('admin.html', questions=questions)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        score = 0
        for i, q in enumerate(questions):
            selected = request.form.get(f'q{i}')
            if selected == q['answer']:
                score += 1

        return render_template('result.html', score=score, total=len(questions))

    return render_template('quiz.html', questions=questions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)