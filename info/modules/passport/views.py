from flask import request, current_app, abort, make_response, jsonify, session
from info import redis_store, constants, db
from info.lib.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_bp
from datetime import datetime
import re


# 图片验证码
# get请求url地址: /passport/image_code?code_id=UUID编码
@passport_bp.route('/image_code')
def get_image_code():
    """获取验证码图片的后端接口"""
    """
    1.获取参数
        1.1 code_id： UUID通用的唯一编码，作为key将验证码真实值存储到redis数据库
    2.校验参数
        2.1 非空判断code_id不能为空
    3.逻辑处理
        3.1 生成验证码图片，验证码图片的真实值
        3.2 code_id作为key将验证码图片的真实值保存到redis数据库，并且设置有效时长(5分钟)
    4.返回值
        4.1 返回验证码图片
    """

    # 1.1 code_id： UUID通用的唯一编码，作为key将验证码真实值存储到redis数据库
    code_id = request.args.get("code_id")

    # 2.1 非空判断code_id不能为空
    if not code_id:
        current_app.logger.error("参数不足")
        abort(404)

    # 3.1 生成验证码图片，验证码图片的真实值
    image_name, real_image_code, image_data = captcha.generate_captcha()

    # 3.2 code_id作为key将验证码图片的真实值保存到redis数据库，并且设置有效时长(5分钟)
    try:
        redis_store.setex("CODEID_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(jsonify(errno=RET.DATAERR, errmsg="保存图片验证码失败"))

    # 4.1 返回验证码图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/JPEG"
    return resp


# 短信验证码
# post请求地址: /passport/sms_code, 参数使用请求体携带
@passport_bp.route('/sms_code', methods=['POST'])
def send_sms_code():
    """发送短信验证码后端接口"""

    """
    1.获取参数
        1.1 mobile: 手机号码， image_code:用户填写的图片验证码，image_code_id:UUID编号
    2.参数校验
        2.1 非空判断
        2.2 手机号码格式正则校验
    3.逻辑处理
        3.1 根据image_code_id编号去redis数据库获取真实的图片验证码值real_image_code
            3.1.1 real_image_code没有值：图片验证码过期了
            3.1.2 real_image_code有值： 将图片验证码从redis中删除（防止多次使用同一个验证码来进行多次验证码）
        3.2 对比用户添加的图片验证码值和真实的图片验证码值是否一致
            3.2.1 不相等：提示图片验证码填写错误，再次生成一张新的图片验证码即可
            3.2.2 相等：发送短信验证码
            
        TODO: 判断用户填写的手机号码是否已经注册（提高用户体验）
        
        3.3 发送短信验证码具体流程
            3.3.1 生成6位的随机短信验证码值
            3.3.2 调用CCP类中方法发送短信验证码
            3.3.3 发送短信验证码失败：提示前端重新发送
            3.3.4 将6位的短信验证码值使用redis数据库保存起来，设置有效时长（方便注册接口获取真实的短信验证值）
    4.返回值
        4.1 发送短信验证码成功  
    """

    # 1.1 mobile: 手机号码， image_code:用户填写的图片验证码，image_code_id:UUID编号(格式: json)
    param_dict = request.json
    mobile = param_dict.get("mobile")
    image_code = param_dict.get("image_code")
    image_code_id = param_dict.get("image_code_id")

    # 2.1 非空判断
    if not all([mobile, image_code, image_code_id]):
        err_dict = {"errno": RET.PARAMERR, "errmsg": "参数不足"}
        """
        {
        "errno": 4103,
        "errmsg": "参数不足"
        }
        """
        return jsonify(err_dict)

    # 2.2 手机号码格式正则校验
    if not re.match("^1[3456789][0-9]{9}$", mobile):
        current_app.logger.error("手机号码格式错误")
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    # 3.1 根据image_code_id编号去redis数据库获取真实的图片验证码值real_image_code
    real_image_code = None
    try:
        real_image_code = redis_store.get("CODEID_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取真实的图片验证码错误")

    # 3.1.1 real_image_code没有值：图片验证码过期了
    if not real_image_code:
        current_app.logger.error("图片验证码过期了")
        return jsonify(errno=RET.NODATA, errmsg="图片验证码过期了")
    # 3.1.2 real_image_code有值： 将图片验证码从redis中删除（防止多次使用同一个验证码来进行多次验证码）
    else:
        try:
            redis_store.delete("CODEID_%s" % image_code_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="删除真实的图片验证码异常")

    """
    细节:
        1.忽略大小写
        2.对比的时候数据格式要一致,将从redis中获取的真实图片验证码值转换成字符串,设置decode_responses=True
    """
    # 3.2 对比用户添加的图片验证码值和真实的图片验证码值是否一致
    if image_code.lower() != real_image_code.lower():
        # 3.2.1 不相等：提示图片验证码填写错误，如果错误代码是4004, 再次生成一张新的图片验证码即可
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码填写错误")

    # 3.2.2 相等：发送短信验证码
    # TODO: 判断用户填写的手机号码是否已经注册（提高用户体验）
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="用户已经注册过")

    # 3.3 发送短信验证码具体流程
    # 3.3.1 生成6位的随机短信验证码值,不足6位前面补0
    import random
    sms_code = "%06d" % random.randint(0, 999999)

    # 3.3.2 调用CCP类中方法发送短信验证码
    # 参数1: 手机号码 参数2: {6位短信验证码, 5分钟过期时长} 参数3:模板编号
    result = CCP().send_template_sms(mobile, {sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)}, 1)

    if result == -1:
        # 3.3.3 发送短信验证码失败：提示前端重新发送
        return jsonify(errno=RET.THIRDERR, errmsg="云通讯发送短信验证码失败")
    elif result == 0:
        # 3.3.4 将6位的短信验证码值使用redis数据库保存起来，设置有效时长（方便注册接口获取真实的短信验证值）
        redis_store.setex("SMS_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

    # 4.1 发送短信验证码成功
    return jsonify(errno=RET.OK, errmsg="发送短信验证码成功")


# 注册
# post请求地址: /passport/register, 参数使用请求体携带
@passport_bp.route('/register', methods=['POST'])
def register():
    """注册后端端口实现"""

    """
    1.获取参数
        1.1 mobile:手机号码 ，sms_code:用户填写的短信验证码，password:未加密的密码  数据格式：json
    2.参数校验
        2.1 非空判断
        2.2 手机号码格式判断
    3.逻辑处理
        3.1 根据手机号码获取redis中的真实的短信验证码值real_sms_code
            3.1.1 real_sms_code有值： 从redis数据库中删除
            3.1.2 real_sms_code没有值：短信验证码过期了
        3.2 对比用户填写的短信验证码值和真实的短信验证码值是否一致
            3.2.1 不相等： 提示短信验证码填写错误
            3.2.2 相等：注册
        3.3 创建用户对象，并给各个属性赋值
        3.4 将用户存储到数据库
        3.5 注册成功代表登录成功，记录用户登录信息到session中
    4.返回值
    """

    # 1.获取参数
    # 1.1 mobile:手机号码 ，sms_code:用户填写的短信验证码，password:未加密的密码  数据格式：json
    params_dict = request.json
    mobile = params_dict.get("mobile")
    sms_code = params_dict.get("sms_code")
    password = params_dict.get("password")

    # 2.参数校验
    # 2.1 非空判断
    if not all([mobile, sms_code, password]):
        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    # 2.2 手机号码格式判断
    if not re.match("^1[345678][0-9]{9}$", mobile):
        current_app.logger.error("手机号码格式错误")
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    # 3.逻辑处理
    # 3.1 根据手机号码获取redis中的真实的短信验证码值real_sms_code
    try:
        real_sms_code = redis_store.get("SMS_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取真实的手机验证码异常")

    if not real_sms_code:
        current_app.logger.error("短信验证码过期了")
        return jsonify(errno=RET.NODATA, errmsg="短信验证码过期了")
    else:
        redis_store.delete("SMS_%s" % mobile)

    # 3.2 对比用户填写的短信验证码值和真实的短信验证码值是否一致
    if sms_code != real_sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码填写错误")

    # 相等则注册用户
    user = User()
    user.mobile = mobile
    # 默认昵称为mobile
    user.nick_name = mobile
    user.last_login = datetime.now()
    # TODO: 密码加密处理并且赋值
    # user.set_hashpassword(password)
    user.password = password

    # 3.4 将用户存储到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="添加用户对象到数据库异常")

    # 3.5 注册成功代表登录成功，记录用户登录信息到session中
    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["nick_name"] = user.nick_name

    # 4.注册成功
    return jsonify(errno=RET.OK, errmsg="注册成功")


# 登录
# post请求地址: /passport/login, 参数使用请求体携带
@passport_bp.route('/login', methods=['POST'])
def login():
    """用户登录的后端接口"""
    """
    1.获取参数
        1.1 mobile:手机号码， password：未加密的密码
    2.校验参数
        2.1 非空判断
        2.2 手机号码格式判断
    3.逻辑处理
        3.1 根据手机号码去查询当前用户user
        3.2 使用user对象判断用户填写的密码是否跟数据库里的一致
        3.3 使用session记录用户登录信息
        3.4 修改用户最后一次登录时间
    4.返回值
    """
    # 获取参数
    params_dict = request.json
    mobile = params_dict.get("mobile")
    password = params_dict.get("password")

    # 参数校验
    if not all([mobile, password]):
        current_app.logger.error("参数不足")
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not re.match("^1[345678][0-9]{9}$", mobile):
        current_app.logger.error("手机号码格式错误")
        return jsonify(errno=RET.PARAMERR, errmsg="手机号码格式错误")

    # 逻辑处理
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户对象异常")

    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")

    if not user.check_passowrd(password):
        return jsonify(errno=RET.DATAERR, errmsg="密码填写错误")

    # 3.3 使用session记录用户登录信息
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    # 3.4 修改用户最后一次登录时间
    user.last_login = datetime.now()

    # 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户对象到数据库异常")

    # 返回登录成功
    return jsonify(errno=RET.OK, errmsg="登录成功")


# 退出
# post请求地址: /passport/logout, 参数使用请求体携带
@passport_bp.route('/logout', methods=['POST'])
def logout():
    """退出登录接口"""

    # 删除session中的用户数据即可
    session.pop("user_id", None)
    session.pop("mobile", None)
    session.pop("nick_name", None)

    # 注意: 管理员用户退出登录的时候需要删除数据
    session.pop("is_admin", False)

    return jsonify(errno=RET.OK, errmsg="退出登录成功")
