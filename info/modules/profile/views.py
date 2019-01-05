from flask import g, render_template
from info import get_user_data
from . import profile_bp


# 127.0.0.1:5000/user/info ---> 个人中心页面
@profile_bp.route('/info')
@get_user_data
def user_info():
    """展示个人中心页面"""
    user = g.user
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template("profile/user.html", data=data)

