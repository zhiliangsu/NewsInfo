from flask import current_app, jsonify
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from info.models import User
from info.utils.response_code import RET

# 从单一职责的原则考虑,manage文件单独作为项目启动文件即可,其他配置可以抽取出去
# app, db, redis_store = create_app("development")
app = create_app("development")

# 6.创建管理对象,将app对象交给管理对象管理起来
manager = Manager(app)

# 7.数据库迁移初始化
Migrate(app, db)

# 8.添加迁移命令
manager.add_command("db", MigrateCommand)

"""
使用方法:
    创建管理员: python manage.py create_admin -n "admin" -p "admin"
    删除管理员: python manage.py create_admin -d "admin"
"""


# 9.自定义创建管理员用户的方法
@manager.option("-n", "--name", dest="name")
@manager.option("-p", "--password", dest="password")
@manager.option("-d", "--delete", dest="delete_user")
def create_admin(name, password, delete_user=None):
    """
    创建管理员用户
    :param name: 账号
    :param password: 密码
    :param delete_user: 要删除的用户账号
    :return:
    """
    # 1.获取参数
    # 2.参数校验
    if not delete_user:
        if not all([name, password]):
            print("参数不足")
            return

        # 3.创建管理员用户对象,并保存到数据库
        admin_user = User()
        admin_user.mobile = name
        admin_user.password = password
        admin_user.nick_name = name
        # 代表创建的是一个管理员用户
        admin_user.is_admin = True

        try:
            db.session.add(admin_user)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="保存管理员用户对象异常")
        print("创建管理员用户成功")

    else:
        try:
            db.session.delete(User.query.filter(User.mobile == delete_user).first())
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(errno=RET.DBERR, errmsg="删除管理员用户对象异常")
        print("删除管理员用户成功")


if __name__ == '__main__':
    # 9.使用manager对象启动flask项目,代替app.run()
    manager.run()
