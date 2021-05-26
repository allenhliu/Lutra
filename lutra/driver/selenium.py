# coding:utf-8
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.touch_actions import TouchActions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import UnexpectedAlertPresentException
from ..util import logging, html_unescape, Assert
from allure import step, attach, attachment_type
from urllib.parse import urljoin
from urllib3.exceptions import ProtocolError
from functools import wraps
import numpy as np
import time
import cv2


def fail_to_snapshot(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        # 有弹窗时，必须关闭弹窗才能截图
        except Exception as e:
            if isinstance(e, UnexpectedAlertPresentException):
                # 如果关了再弹，就继续关，最多三次机会
                tries = 3
                while tries > 0:
                    try:
                        self.webdriver.switch_to.alert.accept()
                        attach(
                            self.webdriver.get_screenshot_as_png(),
                            name="弹窗导致失败后截图",
                            attachment_type=attachment_type.PNG
                        )
                        for entry in self.webdriver.get_log('browser'):
                            if entry['level'] == 'SEVERE':
                                logging.error(str(entry))
                            elif entry['level'] == 'WARNING':
                                logging.warning(str(entry))
                            else:
                                logging.info(str(entry))
                        break
                    except Exception:
                        tries -= 1
            else:
                attach(self.webdriver.get_screenshot_as_png(), name="失败后截图", attachment_type=attachment_type.PNG)
                for entry in self.webdriver.get_log('browser'):
                    if entry['level'] == 'SEVERE':
                        logging.error(str(entry))
                    elif entry['level'] == 'WARNING':
                        logging.warning(str(entry))
                    else:
                        logging.info(str(entry))
            raise e
    return wrapper


class Expect:
    exist = ec.presence_of_element_located
    visible = ec.visibility_of_element_located
    invisible = ec.invisibility_of_element_located
    selected = ec.element_located_to_be_selected
    clickable = ec.element_to_be_clickable
    text = ec.text_to_be_present_in_element

    class URL:
        changes = ec.url_changes
        contains = ec.url_contains
        matches = ec.url_matches
        be = ec.url_to_be

    class Title:
        be = ec.title_is
        contains = ec.title_contains


class XP:
    @classmethod
    def by_to_xpath(cls, by):
        if isinstance(by, str):
            # 用于兼容，字符串就直接返回
            return by
        # 对于 Selenium 定位信息，进行转换
        if by[0] == By.XPATH:
            return by[1]
        elif by[0] == By.CLASS_NAME:
            return cls.class_name(by[1])
        elif by[0] == By.ID:
            return cls.id(by[1])
        elif by[0] == By.NAME:
            return cls.name(by[1])
        elif by[0] == By.LINK_TEXT:
            return cls.partial_text(by[1], tag='a')
        elif by[0] == By.PARTIAL_LINK_TEXT:
            return cls.partial_text(by[1], tag='a')
        elif by[0] == By.TAG_NAME:
            return cls.tag(by[1])
        elif by[0] == By.CSS_SELECTOR:
            raise Exception('CSS 选择器定位信息无法转换成 XPath，请独立使用该元素，或者改成其他定位方式')
        else:
            raise Exception('无法转换成 XPath，或者使用了非法定位信息')

    @classmethod
    def convert_locator_to_xpath(cls, locator):
        while isinstance(locator, tuple):
            if len(locator) == 1:
                # 只剩一个字符串，就是 XPATH
                locator = locator[0]
                break
            if locator[0] in vars(By).values():
                # 第一个串是 By 的成员，说明是 Selenium 定位信息，转换成 XPATH
                locator = cls.by_to_xpath(locator)
            else:
                # 否则，说明第一个字符串是 Lutra 元素的名字信息（meta），干掉它
                locator = locator[1:]
        return locator

    @classmethod
    def attr(cls, attr, value, scope='', relative=True, sibling=None, nth=1, tag='*'):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        return '({}{}[@{}="{}"]{})[{}]'.format(scope, tag, attr, value, sibling, nth)

    @classmethod
    def partial_attr(cls, attr, value, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[contains(@{}, "{}"){}]{})[{}]'.format(scope, tag, attr, value, and_xp, sibling, nth)

    @classmethod
    def partial_class_name(cls, class_name, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        return cls.partial_attr("class", class_name, scope, relative, sibling, nth, tag, and_xp)

    @classmethod
    def partial_link(cls, link, scope='', relative=True, sibling=None, nth=1, and_xp=None):
        return cls.partial_attr('href', link, scope, relative, sibling, nth, 'a', and_xp)

    @classmethod
    def text(cls, text, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[text()="{}"{}]{})[{}]'.format(scope, tag, text, and_xp, sibling, nth)

    @classmethod
    def partial_text(cls, text, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[contains(text(), "{}"){}]{})[{}]'.format(scope, tag, text, and_xp, sibling, nth)

    @classmethod
    def partial_style(cls, style, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[contains(@style, "{}")]{})[{}]'.format(scope, tag, style, and_xp, sibling, nth)

    @classmethod
    def id(cls, id_, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[@id="{}"{}]{})[{}]'.format(scope, tag, id_, and_xp, sibling, nth)

    @classmethod
    def class_name(cls, class_name, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[contains(concat(" ", normalize-space(@class), " "), " {} "){}]{})[{}]'.format(
            scope, tag, class_name, and_xp, sibling, nth
        )

    @classmethod
    def name(cls, name, scope='', relative=True, sibling=None, nth=1, tag='*', and_xp=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        and_xp = ' and ' + and_xp if and_xp else ''
        return '({}{}[@name="{}"{}]{})[{}]'.format(scope, tag, name, and_xp, sibling, nth)

    @classmethod
    def title(cls, title, scope='', relative=True, sibling=None, nth=1, tag='*'):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        return '({}{}[@title="{}"]{})[{}]'.format(scope, tag, title, sibling, nth)

    @classmethod
    def nth(cls, n=1, scope='', relative=False, tag='*', sibling=None):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        return '({}{}{})[{}]'.format(scope, tag, sibling, n)

    @classmethod
    def tag(cls, tag, scope='', relative=True, sibling=None, nth=1):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        return '({}{}{})[{}]'.format(scope, tag, sibling, nth)

    @classmethod
    def q_name(cls, q_name, scope='', relative=True, sibling=None, nth=1):
        scope = cls.convert_locator_to_xpath(scope)
        scope += '//' if relative else '/'
        sibling = '[{}]'.format(sibling) if sibling else ''
        return '({}*[name()="{}"]{})[{}]'.format(scope, q_name, sibling, nth)


class UIDriver:
    def __init__(self, browser='chrome', base_url=None, timeout=10, interval=0.1, headless=True,
                 remote_server=None, remote_browser=None, width=1366, height=700, proxy='', bypass='',
                 user_agent=None, mobile_device=None
                 ):
        self.base_url = base_url
        self.timeout = timeout
        self.interval = interval
        self.browser = browser
        self.remote_server = remote_server
        self.remote_browser = remote_browser
        self.headless = headless
        self.webdriver = None
        self.cookie_list = None
        self.width = width
        self.height = height
        self.proxy = proxy
        self.bypass = bypass
        self.lutra_elem = None
        self.user_agent = user_agent
        self.mobile_device = mobile_device
        while timeout >= 0:
            try:
                self.session()
                break
            except ProtocolError as e:
                if timeout > 0:
                    time.sleep(1)
                timeout -= 1
                if timeout < 0:
                    raise e

    def session(self):
        if self.browser == 'safari':
            self.webdriver = webdriver.Safari()
        elif self.browser == 'phantomjs':
            self.webdriver = webdriver.PhantomJS()
        elif self.browser == 'remote':
            capabilities = getattr(DesiredCapabilities, self.remote_browser.upper())
            kwargs = {
                'command_executor': self.remote_server,
                'desired_capabilities': capabilities
            }
            self.webdriver = webdriver.Remote(**kwargs)
        elif self.browser == 'ie':
            self.webdriver = webdriver.Ie()
            # Firefox & Chrome
        elif self.browser == 'firefox':
            options = webdriver.FirefoxOptions()
            try:
                options.headless = self.headless
            except AttributeError:
                options.set_headless(self.headless)
            options.add_argument('--no-sandbox')
            options.add_argument("--window-size={},{}".format(self.width, self.height))
            self.webdriver = webdriver.Firefox(options=options, log_path='geckodriver.log')
        elif self.browser == 'chrome':
            capabilities = DesiredCapabilities.CHROME
            capabilities['loggingPrefs'] = {'browser': 'ALL'}
            capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
            options = webdriver.ChromeOptions()
            try:
                options.headless = self.headless
            except AttributeError:
                options.set_headless(self.headless)
            if self.user_agent:
                options.add_argument('user-agent={}'.format(self.user_agent))
            if self.mobile_device:
                options.add_experimental_option('mobileEmulation', {"deviceName": self.mobile_device})
                # options.add_experimental_option('w3c', False)
            options.add_argument('--no-sandbox')
            options.add_argument('disable-infobars')
            # options.add_argument("--disable-gpu")
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--lang=zh')
            options.add_argument("--window-size={},{}".format(self.width, self.height))
            # options.add_argument('--ignore-certificate-errors')
            if self.proxy:
                options.add_argument('--proxy-server="http={};https={}"'.format(self.proxy, self.proxy))
            if self.bypass:
                options.add_argument('--proxy-bypass-list="{}"'.format(self.bypass))
            self.webdriver = webdriver.Chrome(desired_capabilities=capabilities, options=options)
        self.webdriver.implicitly_wait(self.timeout)
        return self

    @step('开始初始化')
    def arrangement(self):
        return Arrangement(self)

    @step('设置窗口尺寸')
    def set_window_size(self, width, height):
        self.webdriver.set_window_size(width, height)
        return self

    @step('使用当前 base_url 和 cookie 创建 HTTPDriver')
    def http_driver(self, goto=True, url=None):
        from .requests import HTTPDriver
        if goto:
            self.goto(url or self.base_url)
        return HTTPDriver(base_url=self.base_url, cookie_dict=self.get_cookie_dict())

    @step('查找元素，并返回原始的 Selenium 元素')
    def find_selenium_element(self, *args, **kw):
        return self.find(*args, **kw).selenium_elem

    @step('模版匹配')
    def template_match(self, image, similarity=0.8):
        attach(image, name="待匹配的截图", attachment_type=attachment_type.PNG)
        snapshot = self.webdriver.get_screenshot_as_png()
        # snapshot_array = np.asarray(snapshot, dtype=np.float32).astype(np.uint8)
        attach(snapshot, name="待匹配的截图", attachment_type=attachment_type.PNG)
        snapshot_array = np.frombuffer(snapshot, np.uint8)
        src = cv2.imdecode(snapshot_array, cv2.IMREAD_GRAYSCALE)
        template = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(src, template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, _ = cv2.minMaxLoc(res)
        # loc = np.where(res >= similarity)
        logging.info('Try to match images, with the confidence={}>={}'.format(confidence, similarity))
        if confidence < similarity:
            raise Exception('Template match failed')
        return confidence

    @step('Canvas 模版匹配')
    def template_match_for_canvas(self, canvas_id, image, similarity=0.8):
        canvas = self.webdriver.execute_script(
            'var canvas = document.getElementById("linkScreen"); return canvas.toDataURL().substring(22);'.format(
                canvas_id
            )
        )
        import base64
        canvas_decode = base64.b64decode(canvas)
        canvas_array = np.fromstring(canvas_decode, np.uint8)
        src = cv2.imdecode(canvas_array, cv2.COLOR_BGR2GRAY)
        template = cv2.imread(image, cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(src, template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, _ = cv2.minMaxLoc(res)
        # loc = np.where(res >= similarity)
        logging.info('Try to match images, with the confidence={}>={}'.format(confidence, similarity))
        if confidence < similarity:
            raise Exception('Template match failed')
        return confidence

    @step('运行 JavaScript')
    @fail_to_snapshot
    def js(self, script):
        return self.webdriver.execute_script(script)

    @step("刷新")
    @fail_to_snapshot
    def refresh(self):
        self.webdriver.refresh()

    @fail_to_snapshot
    def find(self, locator, until=None, until_not=None, timeout=None, interval=None):
        """
        封装的 LutraElem 元素
        """
        meta = '未命名'
        # 不是 tuple，就是 XPATH
        if not isinstance(locator, tuple):
            locator = By.XPATH, locator
        # 一定是 tuple
        elif locator[0] not in vars(By).values():
            # 第一个参数可能是字符串，即名字
            if len(locator) == 2:
                meta, *locator = locator[0], By.XPATH, locator[1]
            else:
                meta, *locator = locator[0], *locator[1:]
            # 否则就直接可用
        return self._find(meta, locator[0], locator[1], until, until_not, timeout, interval)

    @step("寻找元素")
    def _find(self, meta, by, location, until=None, until_not=None, timeout=None, interval=None):
        locator = by, location
        logging.info('寻找元素：{}，定位信息：{} = {}'.format(meta, *locator))
        interval = float(self.interval if interval is None else interval)
        time.sleep(interval)
        # self.snapshot()
        if until is Expect.invisible:
            self.webdriver.implicitly_wait(0)
            WebDriverWait(self.webdriver, int(timeout or self.timeout)).until(
                until(locator)
            )
            self.webdriver.implicitly_wait(self.timeout)
            return
        elif until:
            element = WebDriverWait(self.webdriver, int(timeout or self.timeout)).until(
                until(locator)
            )
        elif until_not:
            WebDriverWait(self.webdriver, int(timeout or self.timeout)).until_not(
                until_not(locator)
            )
            return
        else:
            element = self.webdriver.find_element(*locator)
        logging.info('元素坐标：{}'.format(element.location))
        self.lutra_elem = Elem(element, self)
        return self.lutra_elem

    @step('关闭并退出浏览器')
    def clean(self, interval=None):
        interval = float(self.interval if interval is None else interval)
        time.sleep(interval)
        if self.browser != 'safari':
            try:
                self.webdriver.close()
            except Exception:
                pass
        try:
            self.webdriver.quit()
        except Exception:
            pass

    @step('访问 URL')
    def goto(self, url=None, interval=None):
        interval = float(self.interval if interval is None else interval)
        time.sleep(interval)
        url = urljoin(self.base_url, url)
        self.webdriver.get(url)
        # assert self.webdriver.current_url == url
        return self

    @step('全局隐式等待')
    def implicitly_wait(self, second=10):
        self.timeout = second
        self.webdriver.implicitly_wait(second)
        return self

    @step('等待特定秒数')
    def sleep(self, second=1):
        time.sleep(second)
        return self

    @step('保存截图到文件')
    def save_snapshot(self, filename):
        self.webdriver.save_screenshot(filename)
        return self

    @step('截图')
    def snapshot(self):
        attach(self.webdriver.get_screenshot_as_png(), name="截图", attachment_type=attachment_type.PNG)
        return self

    @step('获取 Cookies 词典')
    def get_cookie_dict(self):
        cookie_list = self.webdriver.get_cookies()
        return {item['name']: item['value'] for item in cookie_list}

    @step('获取 Cookies 列表')
    def get_cookie_list(self):
        return self.webdriver.get_cookies()

    @step('使用给定的 Cookies 列表设置 Cookies')
    def set_cookies(self, cookie_list):
        # self.webdriver.delete_all_cookies()
        for item in cookie_list:
            self.webdriver.add_cookie({'name': item['name'], 'value': item['value']})
            # self.webdriver.add_cookie(item)
        return self

    @step('保存 Cookies')
    def save_cookies(self):
        self.cookie_list = self.webdriver.get_cookies()
        return self

    @step('加载已保存的 Cookies')
    def load_cookies(self):
        # self.webdriver.delete_all_cookies()
        for item in self.cookie_list:
            self.webdriver.add_cookie({'name': item['name'], 'value': item['value']})
        return self

    @step('删除所有的 Cookies')
    def delete_all_cookies(self):
        self.webdriver.delete_all_cookies()

    @step('网页源代码')
    def page_source(self):
        return self.webdriver.page_source

    @step('前进')
    def forward(self):
        self.webdriver.forward()
        return self

    @step('后退')
    def back(self):
        self.webdriver.back()
        return self

    @step('切换到指定的 iframe 中')
    def switch_to_frame(self, elem):
        if isinstance(elem, Elem):
            elem = elem.selenium_elem
        self.webdriver.switch_to.frame(elem)
        return self

    @step('切换到缺省的 iframe 中')
    def switch_to_default_frame(self, elem):
        if isinstance(elem, Elem):
            elem = elem.selenium_elem
        self.webdriver.switch_to.default_content(elem)
        return self

    @step('切换到父 iframe 中')
    def switch_to_parent_frame(self, elem):
        if isinstance(elem, Elem):
            elem = elem.selenium_elem
        self.webdriver.switch_to.parent_frame(elem)
        return self

    @step('获取当前页面的 URL')
    def get_url(self):
        return self.webdriver.current_url

    # 在上一个定位的的元素上操作
    def hover(self, interval=None):
        self.lutra_elem.hover(interval=interval)
        return self

    def clear(self, interval=None):
        self.lutra_elem.clear(interval=interval)
        return self

    def clear_text(self, interval=None):
        self.lutra_elem.clear_text(interval=interval)
        return self

    def input(self, text, interval=None):
        self.lutra_elem.input(text=text, interval=interval)
        return self

    def input_sensitive(self, text, interval=None):
        self.lutra_elem.input_sensitive(text=text, interval=interval)
        return self

    def press(self, key_text, interval=None, times=1):
        self.lutra_elem.press(key_text=key_text, interval=interval, times=times)
        return self

    def click(self, interval=None):
        self.lutra_elem.click(interval=interval)
        return self

    def tap(self, interval=None):
        self.lutra_elem.tap(interval=interval)
        return self

    def long_press(self, interval=None):
        self.lutra_elem.long_press(interval=interval)
        return self

    def click_mouse(self, interval=None, no_element=False):
        self.lutra_elem.click_mouse(interval=interval, no_element=no_element)
        return self

    @step('模拟键盘输入')
    @fail_to_snapshot
    def input_keyboard(self, text, interval=None):
        time.sleep(float(interval or self.interval))
        ActionChains(self.webdriver).send_keys(text).perform()
        return self

    def submit(self, interval=None):
        self.lutra_elem.submit(interval=interval)
        return self

    def select(self, value=None, index=None, visible_text=None, interval=None):
        self.lutra_elem.select(value, index, visible_text, interval)
        return self

    def drag_and_drop(self, lutra_elem_to_drop, interval=None):
        """
        Selenium 原生拖拽
        :return: Elem 对象自身
        """
        self.lutra_elem.drag_and_drop(lutra_elem_to_drop, interval)
        return self

    def drag_and_drop_by_offset(self, xoffset=0, yoffset=0, interval=None):
        """
        Selenium 原生拖拽
        :return: Elem 对象自身
        """
        self.lutra_elem.drag_and_drop_by_offset(xoffset, yoffset, interval)
        return self

    def drag_move_release_by_offset(self, xoffset=0, yoffset=0, interval=None):
        """
        Lutra 拖拽
        :return: Elem 对象自身
        """
        self.lutra_elem.drag_move_release_by_offset(xoffset, yoffset, interval)
        return self

    def drag_move_release(self, lutra_elem_to_drop, xoffset=None, yoffset=None, interval=None):
        """
        Lutra 拖拽
        :return: Elem 对象自身
        """
        self.lutra_elem.drag_move_release(lutra_elem_to_drop, xoffset, yoffset, interval)
        return self


class Elem:
    """
    页面元素类, 支持流式调用
    """
    def __init__(self, selenium_elem, driver: UIDriver):
        self.selenium_elem = selenium_elem
        self.driver = driver
        self.webdriver = driver.webdriver

    @step('返回 lutra 驱动的实例')
    def get_driver(self):
        return self.driver

    def find(self, *args, **kwargs):
        return self.driver.find(*args, **kwargs)

    def snapshot(self):
        self.driver.snapshot()

    @fail_to_snapshot
    @step('select 选择选项')
    def select(self, value=None, index=None, visible_text=None, interval=None):
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        select = Select(self.selenium_elem)
        if value:
            select.select_by_value(value)
        if index:
            select.select_by_index(index)
        if visible_text:
            select.select_by_visible_text(visible_text)
        return self

    @fail_to_snapshot
    @step('select 反选选项')
    def deselect(self, deselect_all=False, value=None, index=None, visible_text=None, interval=None):
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        select = Select(self.selenium_elem)
        if deselect_all:
            select.deselect_all()
        if value:
            select.deselect_by_value(value)
        if index:
            select.deselect_by_index(index)
        if visible_text:
            select.deselect_by_visible_text(visible_text)
        return self

    @fail_to_snapshot
    @step('鼠标悬停')
    def hover(self, xoffset=None, yoffset=None, interval=None):
        """
        鼠标悬停
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        if xoffset is not None and yoffset is not None:
            ActionChains(
                self.driver.webdriver
            ).move_to_element_with_offset(
                self.selenium_elem, xoffset, yoffset
            ).perform()
        else:
            ActionChains(self.driver.webdriver).move_to_element(self.selenium_elem).perform()
        return self

    @fail_to_snapshot
    @step('清空文本框')
    def clear(self, interval=None):
        """
        清空文本框
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.selenium_elem.clear()
        return self

    @fail_to_snapshot
    @step('清空文本框')
    def clear_text(self, interval=None):
        """
        清空文本框
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        length = len(self.selenium_elem.get_attribute('value'))
        self.selenium_elem.send_keys(length * Keys.BACKSPACE)
        return self

    @fail_to_snapshot
    @step('输入文字')
    def input(self, text, interval=None):
        """
        输入文字
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.selenium_elem.send_keys(text)
        return self

    @fail_to_snapshot
    def input_sensitive(self, sensitive_text, interval=None):
        """
        输入敏感文字
        :return: Elem 对象自身
        """
        with step('输入敏感文字'):
            interval = float(self.driver.interval if interval is None else interval)
            time.sleep(interval)
            self.selenium_elem.send_keys(sensitive_text)
        return self

    @fail_to_snapshot
    @step('按键')
    def press(self, key_text, interval=None, times=1):
        """
        按键
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.selenium_elem.send_keys(times * getattr(Keys, key_text.upper()))
        return self

    @fail_to_snapshot
    @step('点击')
    def click(self, interval=None):
        """
        点击
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.selenium_elem.click()
        return self

    @fail_to_snapshot
    @step('模拟鼠标点击')
    def click_mouse(self, interval=None, no_element=False):
        """
        点击
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        ActionChains(self.driver.webdriver).click(None if no_element else self.selenium_elem).perform()
        # driver.webdriver.execute_script("$(arguments[0]).click();", self.selenium_elem)
        return self

    @fail_to_snapshot
    @step('模拟手指触摸')
    def tap(self, interval=None):
        """
        点击
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(1 + interval)
        TouchActions(self.driver.webdriver).tap(self.selenium_elem).perform()
        return self

    @fail_to_snapshot
    @step('模拟手指长按')
    def long_press(self, interval=None):
        """
        点击
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        TouchActions(self.driver.webdriver).long_press(self.selenium_elem).perform()
        # driver.webdriver.execute_script("$(arguments[0]).click();", self.selenium_elem)
        return self

    @fail_to_snapshot
    @step('拖砖元素到另一个元素')
    def drag_and_drop(self, lutra_elem_to_drop, interval=None):
        """
        Selenium 原生拖拽
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        ActionChains(self.driver.webdriver).\
            drag_and_drop(self.selenium_elem, lutra_elem_to_drop.selenium_elem).\
            perform()
        return self

    @fail_to_snapshot
    @step('Selenium 原生拖拽-按目标元素')
    def drag_and_drop_by_offset(self, xoffset=0, yoffset=0, interval=None):
        """
        Selenium 原生拖拽
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        ActionChains(self.driver.webdriver).drag_and_drop_by_offset(self.selenium_elem, xoffset, yoffset).perform()
        return self

    @fail_to_snapshot
    @step('Lutra 鼠标拖拽')
    def drag_move_release_by_offset(self, xoffset=0, yoffset=0, interval=None):
        """
        Lutra 拖拽
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        action = ActionChains(self.driver.webdriver)
        action.move_to_element(self.selenium_elem). \
            click_and_hold(self.selenium_elem). \
            pause(interval)
        for i in range(xoffset):
            logging.info("横向第 {} 次移动".format(i))
            action.move_by_offset(i, 0).perform()
        for i in range(yoffset):
            logging.info("纵向第 {} 次移动".format(i))
            action.move_by_offset(0, i).perform()
        action.release(self.selenium_elem).perform()
        return self

    @fail_to_snapshot
    @step('Lutra 鼠标拖拽元素到另一个元素')
    def drag_move_release(self, lutra_elem_to_drop, xoffset=None, yoffset=None, interval=None):
        """
        Lutra 拖拽
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        action = ActionChains(self.driver.webdriver)
        action.move_to_element(self.selenium_elem). \
            click_and_hold(self.selenium_elem). \
            pause(interval)
        if xoffset is None and yoffset is None:
            action.move_to_element(lutra_elem_to_drop.selenium_elem)
        else:
            action.move_to_element_with_offset(lutra_elem_to_drop.selenium_elem, xoffset, yoffset)
        action.release(self.selenium_elem).perform()
        return self

    @fail_to_snapshot
    @step('Lutra 手指拖拽元素到另一个元素')
    def tap_move_release(self, lutra_elem_to_drop, xoffset=None, yoffset=None, interval=None):
        """
        Lutra 拖拽
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)

        src = self.selenium_elem.location
        dest = lutra_elem_to_drop.selenium_elem.location

        action = TouchActions(self.driver.webdriver)
        action.tap_and_hold(src['x'], src['y'])
        if xoffset is None and yoffset is None:
            action.release(dest['x'], dest['y'])
        else:
            action.release(dest['x'] + xoffset, dest['y'] + yoffset)
        action.perform()
        return self

    @fail_to_snapshot
    @step('Lutra 手指拖拽元素')
    def tap_move_release_by_offset(self, xoffset=0, yoffset=0, interval=None):
        """
        Lutra 拖拽
        :return: Elem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)

        src = self.selenium_elem.location
        src_x, src_y = int(src['x']), int(src['y'])
        logging.info('{},{}'.format(src_x, src_y))
        action = TouchActions(self.driver.webdriver)
        action.tap_and_hold(src_x, src_y)
        action.move(src_x + xoffset, src_y + yoffset)
        action.release(src_x + xoffset, src_y + yoffset)
        action.perform()
        return self

    def input_keyboard(self, text, interval=None):
        self.driver.input_keyboard(text, interval=interval)
        return self

    @fail_to_snapshot
    @step('提交')
    def submit(self, interval=None):
        """
        提交
        :return: LutraElem 对象自身
        """
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.selenium_elem.submit()
        return self

    @fail_to_snapshot
    @step('切换到 iframe')
    def switch_to_frame(self, interval=None):
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.webdriver.switch_to.frame(self.selenium_elem)
        return self

    @fail_to_snapshot
    @step('切换到缺省 iframe')
    def switch_to_default_frame(self, interval=None):
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.webdriver.switch_to.default_content(self.selenium_elem)
        return self

    @fail_to_snapshot
    @step('切换到父 iframe')
    def switch_to_parent_frame(self, interval=None):
        interval = float(self.driver.interval if interval is None else interval)
        time.sleep(interval)
        self.webdriver.switch_to.parent_frame(self.selenium_elem)
        return self

    @step('等待特定秒数')
    def sleep(self, second=1):
        """
        Just Wait
        :param second:
        :return:  Elem 对象自身
        """
        time.sleep(second)
        return self

    @step('开始提取')
    def extraction(self):
        return Extraction(self)

    @step('开始断言')
    def assertion(self):
        return Assertion(self)

    @step('key 应为「真」')
    def assert_true(self, key, timeout=None):
        """
        断言 key should be True
        """
        logging.info('Asserting {} be True'.format(key))
        if key in ('id', 'text', 'tag_name', 'size', 'is_displayed', 'is_enabled', 'is_selected'):
            WebDriverWait(self.webdriver, int(timeout or self.driver.timeout)).until(
                lambda x: getattr(self.selenium_elem, key) is not False
            )
        else:
            WebDriverWait(self.webdriver, int(timeout or self.driver.timeout)).until(
                lambda x: self.selenium_elem.get_attribute(key) is not False
            )
        return self

    @step('key 应包含')
    def assert_contain(self, key, value, timeout=None):
        """
        断言 key should contain value
        """
        logging.info('Asserting {} contains {}'.format(key, value))
        if key in ('id', 'text', 'tag_name', 'size', 'is_displayed', 'is_enabled', 'is_selected'):
            WebDriverWait(self.webdriver, int(timeout or self.driver.timeout)).until(
                lambda x: value in getattr(self.selenium_elem, key)
            )
        else:
            WebDriverWait(self.webdriver, int(timeout or self.driver.timeout)).until(
                lambda x: value in self.selenium_elem.get_attribute(key)
            )
        return self

    @step('key 应为')
    def assert_be(self, key, value, timeout=None):
        """
        断言 key should be value
        """
        logging.info('Asserting {} be {}'.format(key, value))
        if key in ('id', 'text', 'tag_name', 'size', 'is_displayed', 'is_enabled', 'is_selected'):
            WebDriverWait(self.webdriver, int(timeout or self.driver.timeout)).until(
                lambda x: getattr(self.selenium_elem, key) == value
            )
        else:
            WebDriverWait(self.webdriver, int(timeout or self.driver.timeout)).until(
                lambda x: self.selenium_elem.get_attribute(key) == value
            )
        return self

    @step('获取特性 attribute')
    def get_attribute(self, name):
        return self.selenium_elem.get_attribute(name)

    @step('获取属性 property')
    def get_property(self, name):
        return self.selenium_elem.get_property(name)


class Arrangement:
    def __init__(self, driver: UIDriver):
        self.driver = driver

    @step('设置 Base URL')
    def base_url(self, base_url):
        self.driver.base_url = base_url
        return self

    @step('设置全局超时时间')
    def timeout(self, timeout):
        self.driver.timeout = timeout
        return self

    @step('设置全局操作等待')
    def interval(self, interval):
        self.driver.interval = interval
        return self

    @step('设置浏览器')
    def browser(self, browser):
        self.driver.browser = browser
        return self

    @step('设置远端服务器')
    def remote_driver(self, remote_server):
        self.driver.remote_server = remote_server
        return self

    @step('设置远端浏览器')
    def remote_browser(self, remote_browser):
        self.driver.remote_browser = remote_browser
        return self

    @step('设置无头模式')
    def headless(self, headless: bool):
        self.driver.headless = headless
        return self

    @step('设置 webdriver')
    def webdriver(self, new_webdriver):
        self.driver.webdriver = new_webdriver
        return self

    @step('设置 cookies')
    def cookie_list(self, cookie_list):
        self.driver.cookie_list = cookie_list
        return self

    @step('设置宽度')
    def width(self, width):
        self.driver.width = width
        return self

    @step('设置高度')
    def height(self, height):
        self.driver.height = height
        return self

    @step('设置代理')
    def proxy(self, proxy):
        self.driver.proxy = proxy
        return self

    @step('设置不代理的地址')
    def bypass(self, bypass):
        self.driver.bypass = bypass
        return self

    @step('启动浏览器')
    def start(self):
        self.driver.session()
        return self


class Assertion:
    def __init__(self, elem: Elem):
        self.elem = elem
        self.selenium_elem = elem.selenium_elem

    @step
    def id(self, assert_method, timeout=None):
        logging.info('Assert id:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.id))
            )
        else:
            assert_method(self.selenium_elem.id)
        return self

    @step
    def displayed_text(self, assert_method, timeout=None):
        logging.info('Assert text:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.text))
            )
        else:
            assert_method(self.selenium_elem.text)
        return self

    @step
    def text(self, assert_method, timeout=None):
        logging.info('Assert text:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.get_attribute('innerText').strip()))
            )
        else:
            assert_method(self.selenium_elem.get_attribute('innerText').strip())
        return self

    @step
    def tag_name(self, assert_method, timeout=None):
        logging.info('Assert tag_name:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.tag_name))
            )
        else:
            assert_method(self.selenium_elem.tag_name)
        return self

    @step
    def size(self, assert_method, timeout=None):
        logging.info('Assert size:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.size))
            )
        else:
            assert_method(self.selenium_elem.size)
        return self

    @step
    def displayed(self, assert_method, timeout=None):
        logging.info('Assert displayed:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.is_displayed))
            )
        else:
            assert_method(self.selenium_elem.is_displayed)
        return self

    @step
    def enabled(self, assert_method, timeout=None):
        logging.info('Assert enabled:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.is_enabled()))
            )
        else:
            assert_method(self.selenium_elem.is_enabled)
        return self

    @step
    def selected(self, assert_method, timeout=None):
        logging.info('Assert selected:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.is_selected()))
            )
        else:
            assert_method(self.selenium_elem.is_selected)
        return self

    @step
    def attribute(self, assert_method, key, timeout=None):
        logging.info('Assert attribute:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(self.selenium_elem.get_attribute(key)))
            )
        else:
            assert_method(self.selenium_elem.get_attribute(key))
        return self

    @step
    def all_selected_options_text(self, assert_method, timeout=None):
        logging.info('Assert all_selected_options_text:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(Select(self.selenium_elem).all_selected_options))
            )
        else:
            assert_method(self.selenium_elem.all_selected_options)
        return self

    @step
    def first_selected_option_text(self, assert_method, timeout=None):
        logging.info('Assert first_selected_option_text:')
        timeout = int(timeout or self.elem.driver.timeout)
        if timeout:
            WebDriverWait(self.elem.webdriver, timeout).until(
                lambda x: Assert.bool(assert_method(Select(self.selenium_elem).first_selected_option.text))
            )
        else:
            assert_method(self.selenium_elem.first_selected_option.text)
        return self

    @step
    def action(self):
        return self.elem


class Extraction:
    def __init__(self, elem: Elem):
        self.elem = elem
        self.selenium_elem = elem.selenium_elem

    @step
    def id(self):
        return self.selenium_elem.id

    @step
    def displayed_text(self):
        return self.selenium_elem.text

    @step
    def text(self):
        return self.selenium_elem.get_attribute('innerText')

    @step
    def tag_name(self):
        return self.selenium_elem.tag_name

    @step
    def size(self):
        return self.selenium_elem.size

    @step
    def displayed(self):
        return self.selenium_elem.is_displayed()

    @step
    def enabled(self):
        return self.selenium_elem.is_enabled()

    @step
    def selected(self):
        return self.selenium_elem.is_selected()

    @step
    def attribute(self, key):
        return self.selenium_elem.get_attribute(key)

    @step
    def all_selected_options_text(self):
        s = Select(self.selenium_elem)
        return (opt.text for opt in s.all_selected_options)

    @step
    def first_selected_option_text(self):
        s = Select(self.selenium_elem)
        return s.first_selected_option.text

