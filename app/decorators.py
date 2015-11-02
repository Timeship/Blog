#!/usr/bin/env python
# coding=utf-8
from functools import wraps
from flask import abort
from flask.ext.login import current_user
from .models import Permission

def permission_required(permission):
    def decorator(f):
        @wraps(f) #使用了Python标准库中的functools包
                  #调用函数装饰器partial(update_wrapper, wrapped=wrapped, assigned=assigned, updated=updated)的简写
        def decorator_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorator_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)
