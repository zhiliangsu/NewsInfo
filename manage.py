from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app
import logging
from flask import current_app

# 从单一职责的原则考虑,manage文件单独作为项目启动文件即可,其他配置可以抽取出去
# app, db, redis_store = create_app("development")
app = create_app("development")
from info import db, redis_store

# 6.创建管理对象,将app对象交给管理对象管理起来
manager = Manager(app)

# 7.数据库迁移初始化
Migrate(app, db)

# 8.添加迁移命令
manager.add_command("db", MigrateCommand)


@app.route('/')
def index():
    redis_store.set("name", "bryant")
    print(redis_store.get("name"))

    # 日志的使用
    logging.debug("我的debug信息")
    logging.info("我的info信息")
    logging.warning("我的warning信息")
    logging.error("我的error信息")
    logging.critical("我的critical信息")

    # flask中记录日志方法(项目使用这种方式记录)
    current_app.logger.debug("flash记录debug信息")

    return "Hello World!"


if __name__ == '__main__':
    # 9.使用manager对象启动flask项目,代替app.run()
    manager.run()
