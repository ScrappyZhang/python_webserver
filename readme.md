# 基于python实现web服务器

## 功能

本项目采用python实现http请求判断、并转发调用Django。

`webserver.py`为web服务器源文件。http请求网站静态文件(static)则由该服务器处理，动态文件交由Django处理。

## 静态路径配置说明

若网站指定静态文件请求URL为某一特定路径，仅需修改源码处正则表达式位置：

```python
# 静态文件根路径
STATIC_ROOT = './static'
# 处理静态文件
        path_info = re.match(r'^/static/(.*)', self.path).group(1)
```

例如：若url指定静态请求URL均需在真实服务器地址下添加‘`abc/c/`’，则此处正则表达式进行相应的处理；并将服务器静态文件根目录STATIC_ROOT替换为相应的路径即可。

```Python
r'^/abc/c/(.*)'
```

## 两种方式运行

1. 在运行时，目前仓库文件，需要将`webserver.py`和`djangoapi.py`移动到`user_mysite`文件夹下，与`manage.py`在同一文件夹。
2. 可以将`user_mysite`文件夹内新建`__init__.py`使其成为一个`python`包，并修改`djangoapi.py`内如下的一行：

```python
from user_mysite import wsgi
```

将其修改为：

```python
from user_mysite.user_mysite import wsgi
```

