#!/usr/bin/env python
# coding=utf-8
from flask import render_template,url_for,flash,redirect,request
from flask.ext.login import login_user,logout_user,login_required
from . import auth
from .. import db
from ..models import User
from .forms import LoginForm,RegistrationForm
from ..email import send_email
from flask.ext.login import current_user

'''登陆'''
@auth.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.vertify_password(form.password.data):
            login_user(user,form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html',form=form)

'''登出'''
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you have been logged out')
    return redirect(url_for('main.index'))

'''注册'''
@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,'Confirm your account','auth/email/confirm',user=user,token=token)
        flash('A confirmation email has been sent to you by email')
        #flash('you can now login.')
        #return redirect(url_for('auth.login'))
        return redirect(url_for('main.index'))
    return render_template('auth/register.html',form=form)

'''确认用户的账户'''
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('you have confirmed your account,thanks')
    else:
        flash('The confirmation link is Invalid or has expired.')
    return redirect(url_for('main.index'))






