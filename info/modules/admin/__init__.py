from flask import Blueprint

# 1.创建蓝图对象
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 3.让包知道views文件中的视图函数
from info.modules.admin.views import *


# 使用请求勾子函数,在每一次请求之前对用户权限进行判断
@admin_bp.before_request
def is_admin_user():
    """判断是否是管理员用户"""

    # print(request.url)
    if request.url.endswith("/admin/login"):
        # 当第一次访问管理员登录接口,不拦截
        # 当登录管理员登录接口,不拦截
        pass
    else:
        # 拦截url进行用户权限判断
        # 3.如果用户是管理员 --> /admin/管理员首页 不拦截直接进入
        user_id = session.get("user_id")
        is_admin = session.get("is_admin")

        # 要么用户未登录or要么用户不是管理员
        if not user_id or not is_admin:
            # 1.如果是普通用户访问 --> /admin/管理员首页, 拦截并引导到新闻首页
            # 1.如果用户未登录访问 --> /admin/管理员首页, 拦截并引导到新闻首页
            return redirect("/")