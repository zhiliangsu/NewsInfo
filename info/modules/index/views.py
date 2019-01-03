from info.modules.index import index_bp
from flask import current_app, render_template


@index_bp.route('/')
def index():
    # 返回渲染模板文件
    print(current_app.url_map)
    return render_template("news/index.html")


@index_bp.route('/favicon.ico')
def favicon():
    """
    返回网站图标

    Function used internally to send static files from the static
        folder to the browser
    内部用来发送静态文件到浏览器的方法
    """
    return current_app.send_static_file("news/favicon.ico")
