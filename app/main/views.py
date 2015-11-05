#!/usr/bin/env python
# coding=utf-8
from flask import render_template,redirect,url_for,abort,flash,request,current_app
from flask.ext.login import login_required,current_user
from . import main
from .forms import EditProfileForm,EditProfileAdminForm,PostForm
from .. import db
from ..models import Permission,User,Role,Post

#@main.route('/',methods=['GET','POST'])
#def index():
#    form = NameForm()
#    if form.validate_on_submit():
#        #...
#        return redirect(url_for('.index'))
#    return render_template('index.html',
#                           form=form,name=session.get('name'),
#                           known=session.get('known',False),
#                           current_time=datetime.utcnow())
#
'''查看用户信息'''    
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user,posts=posts)

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

'''博客文章'''
@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data,author=current_user._get_current_object())
        #变量current_user由flask-login提供，和所有上下文变量一样，也是通过线程内的代理对象实现
        #这个对象的表现类似用户对象，但实际上是一个轻度包装，包含真正的用户对象，数据库需要真正的用户对象
        #因此需要_get_current_object()
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page',1,type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,\
                                        per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],error_out=False)
    #posts = Post.query.order_by(Post.timestamp.desc()).all() #按时间逆序
    posts = pagination.items
    return render_template('index.html',form=form,posts=posts,pagination=pagination)







