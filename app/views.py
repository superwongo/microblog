from app import app
from flask import render_template, flash, redirect
from .forms import LoginForm


# methods不赋值默认GET
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # flash 函数是一种快速的方式在呈现给用户的页面上显示一个消息
        flash('Login requested for OpenID="' + form.openid.data + '", remember_me=' + str(form.remember_me.data))
        return redirect('/index')
    return render_template("login.html", title='Sing In', form=form, providers=app.config['OPENID_PROVIDERS'])
