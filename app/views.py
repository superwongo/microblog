from flask import render_template, flash, redirect, session, url_for, request, g
from .forms import LoginForm, EditForm
from app import app, db, lm, oid
from flask_login import login_user, logout_user, current_user, login_required
from .models import User
import datetime


@app.route('/')
@app.route('/index')
# 确保了这页只被已经登录的用户看到
@login_required
def index():
    user=g.user
    posts = [
        {
            'author': {'nickname': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'nickname': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)


# methods不赋值默认GET
@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    # Flask 中的 g 全局变量是一个在请求生命周期中用来存储和共享数据
    # 检查g.user是否被设置成一个认证用户，如果是的话将会被重定向到首页
    # 已经登录的用户无需重新登录
    if g.user and g.user.is_authenticated:
        # url_for 函数是定义在 Flask 中，以一种干净的方式为一个给定的视图函数获取 URL
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        # flash 函数是一种快速的方式在呈现给用户的页面上显示一个消息
        # flash('Login requested for OpenID="' + form.openid.data + '", remember_me=' + str(form.remember_me.data))
        # return redirect('/index')

        # flask.session 提供了一个更加复杂的服务对于存储和共享数据。
        # 一旦数据存储在会话对象中，在来自同一客户端的现在和任何以后的请求都是可用的。
        # 数据保持在会话中直到会话被明确地删除。
        session['remember_me'] = form.remember_me.data
        # oid.try_login 被调用是为了触发用户使用 Flask-OpenID 认证
        # OpenID 认证异步发生。如果认证成功的话，Flask-OpenID 将会调用一个注册了 oid.after_login 装饰器的函数。
        # 如果失败的话，用户将会回到登陆页面。
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template("login.html", title='Sing In', form=form, providers=app.config['OPENID_PROVIDERS'])


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@oid.after_login
def after_login(resp):
    if not resp.email or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if not user:
        nickname = resp.nickname
        if not nickname or nickname == "":
            nickname = resp.email.split('@')[0]
        # 让 User 类为我们选择一个唯一的名字
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.before_request
def before_request():
    # 任何使用了 before_request 装饰器的函数在接收请求之前，将当前用户赋值给g.user
    g.user = current_user
    if g.user.is_authenticated:
        g.user.last_seen = datetime.datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<nickname>')
@login_required
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if not user:
        flash('User ' + nickname + ' not found')
        return redirect(url_for('index'))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html', form=form)


@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.tml'), 500
