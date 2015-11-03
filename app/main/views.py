#!/usr/bin/env python
# coding=utf-8
from datetime import datetime
from flask import render_template,session,redirect,url_for,abort,flash
from flask.ext.login import login_required,current_user
from . import main
from .forms import NameForm,EditProfileForm,EditProfileAdminForm
from .. import db
from ..models import User,Role

@main.route('/',methods=['GET','POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        #...
        return redirect(url_for('.index'))
    return render_template('index.html',
                           form=form,name=session.get('name'),
                           known=session.get('known',False),
                           current_time=datetime.utcnow())

'''查看用户信息'''    
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html',user=user)

'''编辑个人资料'''
@main.route('/edit_profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('your profile has been update')
        return redirect(url_for('.user',username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)

'''管理员的资料编辑'''
@main.route('/edit_profile/<int:id>',methods=['GET','POST'])
@login_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id) #如果提供的id不对则返回404错误，flask-sqlalchemy提供的函数
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('the profile has been updated.')
        return redirect(url_for('.user',username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile_admin.html',form=form)









