# -*- coding: utf-8 -*-
import re
import urllib.parse
import logging
from pymysql import connect

# 定义一个字典，形成url与方法名的映射
URL_FUNC_DICT = dict()


# 通用装饰器
def route(url):
    def set_func(func):
        # URL_FUNC_DICT["/index.py"] = index
        URL_FUNC_DICT[url] = func

        def call_func(*args, **kwargs):
            func(*args, **kwargs)
        return call_func
    return set_func


@route(r"/index.html")
def index(ret):
    """股票主页"""
    with open("./templates/index.html",  "r", encoding="utf-8") as f:
         content = f.read()

    # 连接数据库
    conn = connect(host="localhost",port=3306,user="root",password="root", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = """select * from info;"""
    cs.execute(sql)
    stock_infos = cs.fetchall()
    cs.close()
    conn.close()

    # 替换内容
    tr_template = """
        <tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>
                <input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="%s">
            </td>
        </tr>
    """
    html = ""
    for line_info in stock_infos:
        html += tr_template % (line_info[0], line_info[1], line_info[2], line_info[3],
                               line_info[4], line_info[5], line_info[6], line_info[7],
                               line_info[1])

    content = re.sub(r"\{%content%\}", html, content)
    return content


@route(r"/center.html")
def center(ret):
    """个人中心"""
    with open("./templates/center.html", "r", encoding="utf-8") as f:
        content = f.read()
    # 连接数据库
    conn = connect(host="localhost", port=3306, user="root", password="root", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = """select i.code,i.short,i.chg,i.turnover,i.price,i.highs,f.note_info from info as i inner join focus as f on i.id=f.info_id"""
    cs.execute(sql)
    stock_infos = cs.fetchall()
    cs.close()
    conn.close()

    # 替换内容
    tr_template = """
            <tr>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>
                    <a type="button" class="btn btn-default btn-xs" href="/update/%s.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
                </td>
                <td>
                    <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="%s">
                </td>
            </tr>
        """
    html = ""
    for line_info in stock_infos:
        html += tr_template % (line_info[0], line_info[1], line_info[2], line_info[3],
                               line_info[4], line_info[5], line_info[6], line_info[0],
                               line_info[0 ])

    content = re.sub(r"\{%content%\}", html, content)
    return content


@route(r"/update/(\d+)\.html")
def show_update_page(ret):
    """显示修改页面"""
    stock_code = ret.group(1)
    with open("./templates/update.html", "r", encoding="utf-8") as f:
        content = f.read()
    # 连接数据库
    conn = connect(host="localhost", port=3306, user="root", password="root", database="stock_db", charset="utf8")
    cs = conn.cursor()
    sql = """select f.note_info from focus as f inner join info as i on i.id=f.info_id where i.code=%s"""
    cs.execute(sql, (stock_code,))
    stock_infos = cs.fetchone()
    note_info = stock_infos[0]
    cs.close()
    conn.close()

    content = re.sub(r"\{%note_info%\}", note_info, content)
    content = re.sub(r"\{%code%\}", stock_code, content)
    return content


@route(r"/update/(\d+)/(.*)\.html")
def save_update_page(ret):
    """保存修改信息"""
    stock_code = ret.group(1)
    comment = ret.group(2)
    comment = urllib.parse.unquote(comment)

    sql = """update focus set note_info=%s where info_id=(select id from info where code=%s);"""
    conn = connect(host="localhost", port=3306, user="root", password="root", database="stock_db", charset="utf8")
    cs = conn.cursor()
    cs.execute(sql, (comment, stock_code))
    conn.commit()
    cs.close()
    conn.close()
    return "修改成功"


@route(r"/add/(\d+)\.html")
def add_focus(ret):
    """添加股票关注"""
    # 1. 获取股票代码
    stock_code = ret.group(1)

    # 2. 判断试下是否有这个股票代码
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    cs = conn.cursor()
    sql = """select * from info where code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果要是没有这个股票代码，那么就认为是非法的请求
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "没有这支股票，大哥麻烦请手下留情..."

    # 3. 判断以下是否已经关注过
    sql = """ select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果查出来了，那么表示已经关注过
    if cs.fetchone():
        cs.close()
        conn.close()
        return "已经关注过了，请勿重复关注..."

    # 4. 添加关注
    sql = """insert into focus (info_id) select id from info where code=%s;"""
    cs.execute(sql, (stock_code,))
    conn.commit()
    cs.close()
    conn.close()

    return "关注成功...."


@route(r"/del/(\d+)\.html")
def del_focus(ret):
    """取消关注"""
    # 1. 获取股票代码
    stock_code = ret.group(1)

    # 2. 判断试下是否有这个股票代码
    conn = connect(host='localhost', port=3306, user='root', password='root', database='stock_db', charset='utf8')
    cs = conn.cursor()
    sql = """select * from info where code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果要是没有这个股票代码，那么就认为是非法的请求
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "没有这支股票，大哥 ，我们是创业公司，请手下留情..."

    # 3. 判断以下是否已经关注过
    sql = """ select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;"""
    cs.execute(sql, (stock_code,))
    # 如果查出来了，那么表示已经关注过
    if not cs.fetchone():
        cs.close()
        conn.close()
        return "之前未关注过了，请勿取消关注..."

    # 4. 取消关注
    sql = """delete from focus where info_id=(select id from info where code=%s);"""
    cs.execute(sql, (stock_code,))
    conn.commit()
    cs.close()
    conn.close()

    return "取消关注成功...."


def application(env, start_response):
    start_response('200 OK', [('Content-Type', "text/html;charset=utf-8")])

    file_name = env["PATH_INFO"]
    # file_name = "/index.html"

    logging.basicConfig(level=logging.INFO,
                        filename="./log.txt",
                        filemode="a",
                        format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

    logging.info("访问的是 %s" % file_name)

    try:
        # return URL_FUNC_DICT[file_name]()
        for url, func in URL_FUNC_DICT.items():
            # {
            #     r"/index.html":index,
            #     r"/center.html":center,
            #     r"/add/\d+\.html":add_focus
            # }
            ret = re.match(url, file_name)
            if ret:
                return func(ret)
        else:
            logging.warning("请求的url(%s)没有对应的函数...." % file_name)
            return "请求的url(%s)没有对应的函数...." % file_name
    except Exception as ret:

        return "产生异常:%s" % str(ret)
