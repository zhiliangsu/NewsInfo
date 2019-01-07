from flask import Blueprint

# 1.创建蓝图对象
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 3.让包知道views文件中的视图函数
from info.modules.admin.views import *
