#!/usr/bin/env python
# coding=utf-8
from flask import Blueprint

main = Blueprint('main',__name__)

from .import views,errors
from ..models import Permission

'''使用上下文处理器能让变量在所有模板中可以全局访问
例如{{Permission.ADMINISTER}}
而不必每次在render_template的时候都要多添加一个模板参数
'''
@main.app_context_processor 
def inject_permissions():
    return dict(Permission=Permission)
