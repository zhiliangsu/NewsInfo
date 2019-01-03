

# 过滤器的本质是函数
# 1.使用python的函数实现业务逻辑
def do_index_class(index):
    if index == 1:
        return "first"
    elif index == 2:
        return "second"
    elif index == 3:
        return "third"
    else:
        return ""
