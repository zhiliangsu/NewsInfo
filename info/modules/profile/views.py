from flask import g, render_template, request, jsonify, session, current_app
from info import get_user_data, db, constants
from info.utils.pic_storage import pic_storage
from info.utils.response_code import RET
from . import profile_bp


# 127.0.0.1:5000/user/pic_info ---> 展示修改头像页面&头像数据修改
@profile_bp.route('/pic_info', methods=["POST", "GET"])
@get_user_data
def pic_info():
    """展示修改头像页面&头像数据修改"""

    # GET请求: 返回模板页面,展示修改头像页面
    if request.method == "GET":
        return render_template("profile/user_pic_info.html")

    # POST请求: 提交头像数据并修改保存
    """
    1.获取参数
        1.1 avatar:上传的图片数据, user:当前用户对象
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 调用工具类将图片数据上传带七牛云
        3.1 将返回的图片名称给予avatar_url赋值，并保存回数据库
        3.2 将图片的完整url返回
    4.返回值
    """

    # 1.1 avatar:上传的图片数据, user:当前用户对象
    avatar = request.files.get("avatar")

    # ?
    avatar_data = None
    try:
        avatar_data = avatar.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="图片二进制数据读取失败")

    # 获取当前登录用户
    user = g.user

    # 2.1 非空判断
    if not avatar_data:
        return jsonify(errno=RET.PARAMERR, errmsg="图片数据为空")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 3.0 调用工具类将图片数据上传带七牛云
    try:
        pic_name = pic_storage(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="上传图片到七牛云异常")

    # 3.1 将返回的图片名称给予avatar_url赋值，并保存回数据库
    user.avatar_url = pic_name

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户头像数据异常")

    # 3.2 将图片的完整url返回
    full_url = constants.QINIU_DOMIN_PREFIX + pic_name

    return jsonify(errno=RET.OK, errmsg="上传图片成功", data={"avatar_url": full_url})


# 127.0.0.1:5000/user/base_info ---> 用户基本资料页面
@profile_bp.route('/base_info', methods=["POST", "GET"])
@get_user_data
def base_info():
    """用户基本资料页面"""

    # 获取当前登录用户对象
    user = g.user

    # GET请求: 返回模板页面,展示用户基本资料
    if request.method == "GET":
        data = {"user_info": user.to_dict() if user else None}
        return render_template("profile/user_base_info.html", data=data)

    # POST请求: 修改用户基本资料
    """
    1.获取参数
        1.1 user: 当前登录用户对象， signature:个性签名，nick_name:昵称，gender:性别
    2.校验参数
        2.1 非空判断
        2.2 gender in ["MAN", "WOMAN"]
    3.逻辑处理
        3.0 将当前用户各个属性重新赋值 ，保存到数据库即可
    4.返回值
        登录成功
    """

    # 1.1 user: 当前登录用户对象， signature:个性签名，nick_name:昵称，gender:性别
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    # 2.1 非空判断
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2.2 gender in ["MAN", "WOMAN"]
    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3.0 将当前用户各个属性重新赋值 ，保存到数据库即可
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    # 注意: 修改了nick_name, 会话对象session中保存的数据也需要更新
    session["nick_name"] = nick_name

    # 将上述修改操作保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="修改用户对象基本数据异常")

    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="修改用户基本数据成功")


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
