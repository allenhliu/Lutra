# 介绍

Lutra 自动化测试框架

由 CDC 基于 pytest、allure、selenium、requests 定制

# 用例设计
## 一、用例组织

```
./ # 项目目录
└── test/ # 测试目录
    ├── page/ # 页面模型
    │   ├── common_page.py
    │   └── xx_page.py
    ├── case/ # 测试用例
    │   ├── test_xx.py
    │   └── test_yy.py
    ├── xml_report/ # Allure 测试报告
    ├── config.py # 配置文件
    ├── config_local.py # 本地配置文件，请在 .gitignore 中忽略
    └── requirements.txt # 依赖
```
## 二、页面模型
每个页面模型文件，包含两个定位类、操作类两个类

以 `edit_page.py` 为例：

```python
from selenium.webdriver.common.by import By
from lutra.driver.selenium import XP, Expect
from .common_page import CommonPageElem, CommonPage
from allure import step


class EditPageElem(CommonPageElem):
    """定位类，无需实例化"""
    pass

class EditPage(CommonPage):
    """操作类，需要实例化"""
    pass

```

### 定位类
定位类包含且仅包含该页面元素的定位信息

定位类要求使用类变量、静态方法和类方法，不必进行实例化

eg:

```python
class EditPageElem(CommonPageElem):
    class Outline:
        """
        大纲
        """
        survey_outline = XP.attr('data-tab', 'survey_outline')
        add_page = XP.class_name('add_page')

        @staticmethod
        def question_item_in_nth_page(title, n):
            return XP.title(title, XP.class_name('outline_page', nth=n))

```

### 操作类
操作类包含且仅包含该页面所能进行的操作方法

操作类要求使用非静态方法，需要进行实例化

使用 allure.step 装饰器定义操作步骤

eg:

```python
class EditPage(CommonPage):
    # 使用 allure.step 装饰器定义步骤
    @step('新建问卷')
    def create_survey(self, goto=True, title):
        d = self.driver
        if goto:
            d.goto('edit.html')
        d.find(EditPageElem.Editor.title, Expect.visible).click().input(title, interval=1)
        return self.get_sid(save=True, check_saved=True)
```

## 三、测试用例
测试用例组织由 Lutra Driver 驱动

使用 Lutra 封装的 Assert 类

使用

使用 pytest 的 fixture 装饰器进行 setup 和 teardown

从页面模型的「定位类」中获取静态定位信息

将页面模型「操作类」实例化以进行用例操作

使用 allure.step 的上下文方式，划分用例的预置条件（given）/操作步骤（when）/预期结果（then）

eg:

```python
from lutra.driver.selenium import UIDriver, Expect
from lutra.util import P0, P1, P2, P3, Assert
from allure import severity, step
from pytest import fixture, mark
from random import choice
import config
from page.qqlogin_page import QQLoginPage
from page.edit_page import EditPageElem, EditPage
from page.mine_page import MinePageElem, MinePage


@fixture
def qq_login() -> UIDriver:
    # 登录
    d = UIDriver(
        browser=config.BROWSER,
        headless=config.HEADLESS,
        base_url=config.BASE_URL,
        timeout=config.TIMEOUT,
        interval=config.INTERVAL,
        proxy=config.PROXY,
        bypass=config.BYPASS
    )
    QQLoginPage(d).login(choice(config.UIDS), config.PASSWORD)
    # 用例
    yield d
    # 关闭浏览器和强制关闭浏览器
    d.clean()


class TestEdit:
    @severity(P0)
    def test_copy_question(self, qq_login: UIDriver):
        """
        复制题目
        """
        with step('given'):
            d = qq_login
            # 添加单选题目
            EditPage(d).create_survey(title='test_copy_question')
            EditPage(d).add_question(type_item=EditPageElem.TypeItem.radio, title='test_copy_question')
        with step('when'):
            # 复制题目
            question_item = EditPageElem.Editor.QuestionItem()
            d.find(question_item.question).hover()
            d.find(question_item.copy).click()
        with step('then'):
            # 检查复制
            d.find(EditPageElem.Editor.QuestionItem(2).question, Expect.visible)
            # 检查保存
            sid = EditPage(d).get_sid(check_saved=True)
            # 删除测试数据
            MinePage(d).delete_survey(sid=sid)

```
## 三、配置文件
配置文件的方式建议使用 python 代码的形式，便于使用复杂逻辑

### 通用配置文件

通用配置文件应当放置于代码仓库中，读取环境变量和本地配置文件，不要保存测试账号等敏感信息

config.py

```python
# coding:utf-8
import os
BROWSER = os.environ.get('BROWSER', 'chrome')
HEADLESS = os.environ.get('HEADLESS', 'True') == 'True'
TIMEOUT = int(os.environ.get('TIMEOUT', 10))
INTERVAL = float(os.environ.get('INTERVAL', 0.1))
BASE_URL = os.environ.get('BASE_URL', '')
WIDTH = os.environ.get('WIDTH', '1366')
HEIGHT = os.environ.get('HEIGHT', '700')
UIDS = os.environ.get('UIDS', '').split(',')
PASSWORD = os.environ.get('PASSWORD', '')
REMOTE_SERVER = os.environ.get('REMOTE_SERVER', '')
REMOTE_BROWSER = os.environ.get('REMOTE_BROWSER', '')
PROXY = os.environ.get('PROXY', '')
BYPASS = os.environ.get('BYPASS', '')

try:
    from config_local import *
except ModuleNotFoundError:
    pass


```

### 本地配置文件（可选）

可以使用本地配置文件，方便本地调试，但一定要在 `.gitignore` 中忽略。

config_local.py

```python
# coding:utf-8
# HEADLESS = False
BROWSER = 'chrome'
TIMEOUT = 20
INTERVAL = 0.1
BASE_URL = 'https://wj.qq.com'
WIDTH = '1366'
HEIGHT = '700'
UIDS = '123456789', '987654321'
PASSWORD = 'test_password'
```

## 四、依赖

requirements.txt

```python
git+http://git.code.oa.com/lutra/lutra.git
```
## 五、使用
### Docker（推荐）
Lutra 的镜像已经托管在：
`docker.oa.com/lutra/lutra`
（请联系 jacejiang 添加权限）

请参考以下链接配置 Docker 镜像源：

http://tapd.oa.com/TDW_GAIA/markdown_wikis/#1010096801007961001

http://docker.oa.com/help

执行测试：

```bash
# cd ${WORKSPACE}
# rm -rf test/report test/xml_report
# mkdir -p test/report test/xml_report
docker run --rm -v ${WORKSPACE}/test:/usr/src/test:cached \
    -e "HTTP_PROXY=${HTTP_PROXY}:8080" \
    -e "HTTPS_PROXY=${HTTPS_PROXY}:8080" \
    -e "NO_PROXY=tlinux-mirror.tencent-cloud.com,tlinux-mirrorlist.tencent-cloud.com,localhost,.local,10." \
    -e "BROWSER=chrome" \
    -e "TIMEOUT=30" \
    -e "INTERVAL=0.1" \
    -e "BASE_URL=https://example.com" \
    -e "WIDTH=1366" \
    -e "HEIGHT=768" \
    -e "UIDS=123456789,987654321" \
    -e "PASSWORD=test_password" \
    --shm-size 2g docker.oa.com/lutra/lutra -n 8 --reruns 5
```

说明：

环境变量（包括 HTTP_PROXY 和配置参数等）使用 docker 的 -e 参数传入容器

对于 pytest 的参数，-n 8 意为使用 8 核心并发，--reruns 5 意味失败重试次数为 5

### 本地

本地使用 Python 3.6 以上版本

需要安装 chromedriver 并配置环境变量

生成报表需要 jdk8 和 allure2 环境

请使用虚拟环境运行

#### 安装依赖
(依赖托管在 git.oa.com，请联系 jacejiang 添加 git 仓库权限)
```bash
pip install -r requirements.txt
```

#### 运行

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -W ignore:RemovedInPytest4Warning -n 4 --alluredir=xml_report
```

#### 报表

直接查看

```bash
allure serve xml_report -h 127.0.0.1
```

生成静态报表

```bash
allure generate xml_report -o report --clean
```

### 蓝盾

本质即为 Docker 运行方式，要求使用 Docker 进行环境隔离

#### 预置条件

安装 Docker 并添加内部源：
http://dcloud.oa.com/wiki/cdcim/21053

如有需要，申请开通外网代理：
http://dcloud.oa.com/wiki/cdcim/21073

拉取最新镜像：
`docker pull docker.oa.com/lutra/lutra`


#### 添加自动化测试原子

使用「脚本任务（linux和macOS环境）」

```bash
set -x
cd ${WORKSPACE}
docker run --rm -v ${WORKSPACE}/test:/usr/src/test:cached \
    -e "HTTP_PROXY=${HTTP_PROXY}:8080" \
    -e "HTTPS_PROXY=${HTTPS_PROXY}:8080" \
    -e "NO_PROXY=tlinux-mirror.tencent-cloud.com,tlinux-mirrorlist.tencent-cloud.com,localhost,.local,10.,${DOMAIN}" \
    -e "BROWSER=chrome" \
    -e "TIMEOUT=30" \
    -e "INTERVAL=0.1" \
    -e "BASE_URL=https://${DOMAIN}" \
    -e "WIDTH=1366" \
    -e "HEIGHT=768" \
    -e "UIDS=123456789,987654321" \
    -e "PASSWORD=test_password" \
    --shm-size 2g docker.oa.com/lutra/lutra -n 8 --reruns 5
setEnv "result" "$?"
```

勾选"每行命令运行返回值非零时，继续执行脚本"，以保证失败时仍能正常生成报表


#### 添加报表生成原子

使用「自定义产出物报告」

待展示的产出物报告路径：./test/report

入口文件：index.html


#### 添加执行结果判断原子

使用「脚本任务（linux和macOS环境）」

```bash
if [ ${result} != 0 ];then
echo "❌自动化测试未通过"
echo "请关闭此执行日志，然后点击右上角【产出物报告】，选择【自动化测试报告】，检查失败用例。"
else
echo "✅自动化测试通过"
echo "请关闭此执行日志，然后点击右上角【产出物报告】，选择【自动化测试报告】，查看执行报告。"
fi
echo "http://devops.oa.com/console/pipeline/ur/${pipeline.id}/detail/${pipeline.build.id}/output"
exit ${result}
```

# 框架 API

## 一、Lutra 驱动

Lutra 使用 Driver 的概念来驱使用例的运行，Driver 是对驱动 Lutra 的底层库的二次封装。

常用的 Lutra Driver 包括：

lutra.driver.selenium.UIDriver

lutra.driver.requests.HTTPDriver

在用例的 setUp 方法中，创建 Lutra Driver 的实例，并传递到用例中使用

每个驱动都会定义 arrangment、assertion、extraction 等工厂方法，
调用即进入赋值、断言、抽取的 Step。

在 Driver 对象上调用 arrangment 方法，得到该驱动的 Arrangement 对象，支持各种赋值操作；

```python
d.arrangment().timeout(30)
```

在 Driver 对象上（带参数）调用查找元素/发送请求的方法，得到该驱动的 Elem/Resp 对象，支持各种点击/取值等动作；

```python
d.find(XP.id('test')).click()
```
在 Elem/Resp 对象上调用 assertion/extraction 方法，得到该驱动的 Assertion/Extraction 对象，支持各种断言操作；

在 Driver 对象上调用 assertion/extraction 方法，等同于在上一个返回的 Elem/Resp 对象上调用。

例如： 

```python
d.assertion().text(Assert.contain('test_text'))
```

## 二、Lutra 断言

Lutra 封装了一套与 pytest 和 allure 深度集成的独立断言类:

lutra.util.Assert

使用时，将比较方法对象传入 Lutra Driver 的方法参数中，有两种传入方式：

```python
d.assertion().json(Assert.equal_to, 'status', 1, 'info', 'success')
d.assertion().status_code(Assert.equal_to(200))
```

## 三、其他


