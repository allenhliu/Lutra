# coding:utf-8
import requests
from urllib.parse import urljoin
from ..util import logging, json_parser
from functools import wraps
from allure import step


def fail_to_log(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logging.error(self.response.text)
            raise e

    return wrapper


class HTTPDriver:
    """
    接口 Driver 类, 支持流式调用
    """
    def __init__(self, base_url=None, cookie_dict=None, cookie_list=None, timeout=None, method=None,
                 params=None, data=None, path_params=None, headers=None, proxy=None):
        self.session = requests.Session()
        self.base_url = base_url
        self.params = params
        self.data = data
        self.path_params = path_params
        self.headers = headers
        self.resp: Resp = None
        self.timeout = timeout
        self.method = method
        self.json = None
        self.files = None
        self.proxies = {"http": proxy, "https": proxy} if proxy else None
        # self.assert_mode = None
        # self.assert_value = None
        # self.assert_key = None
        # self.assert_indexes = None
        # self.cookies = cookies
        if cookie_list:
            cookie_dict = {item['name']: item['value'] for item in cookie_list}
        if cookie_dict:
            cookies = requests.utils.cookiejar_from_dict(cookie_dict, cookiejar=None, overwrite=True)
            self.session.cookies = cookies

    @step('开始初始化')
    def arrangement(self):
        return Arrangement(self)

    def assertion(self):
        return self.resp.assertion()

    def extraction(self):
        return self.resp.extraction()

    @step
    def send(self, *args, **kwargs):
        """
        发送合适的请求
        """
        assert self.method in ('get', 'post', 'head', 'options', 'put', 'delete')
        response = getattr(self.session, self.method, *args, **kwargs)
        self.resp = Resp(response, self)
        return self.resp

    @step
    def get(self, url='', **kwargs):
        """
        发送 get 请求
        """
        if '://' not in url:
            url = urljoin(self.base_url, url)
        if self.path_params:
            url = url.format(**self.path_params)
        kwargs['headers'] = kwargs.get('headers', self.headers)
        kwargs['params'] = kwargs.get('params', self.params)
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        kwargs['proxies'] = kwargs.get('timeout', self.proxies)
        response = self.session.get(url, **kwargs)
        self.resp = Resp(response, self)
        return self.resp

    @step
    def head(self, url='', **kwargs):
        """
        发送 head 请求
        """
        if '://' not in url:
            url = urljoin(self.base_url, url)
        if self.path_params:
            url = url.format(**self.path_params)
        kwargs['headers'] = kwargs.get('headers', self.headers)
        kwargs['params'] = kwargs.get('params', self.params)
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        kwargs['proxies'] = kwargs.get('timeout', self.proxies)
        response = self.session.head(url, **kwargs)
        self.resp = Resp(response, self)
        return self.resp

    @step
    def options(self, url='', **kwargs):
        """
        发送 options 请求
        """
        if '://' not in url:
            url = urljoin(self.base_url, url)
        if self.path_params:
            url = url.format(**self.path_params)
        kwargs['headers'] = kwargs.get('headers', self.headers)
        kwargs['params'] = kwargs.get('params', self.params)
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        kwargs['proxies'] = kwargs.get('timeout', self.proxies)
        response = self.session.options(url, **kwargs)
        self.resp = Resp(response, self)
        return self.resp

    @step
    def post(self, url='', **kwargs):
        """
        发送 post 请求
        """
        if '://' not in url:
            url = urljoin(self.base_url, url)
        if self.path_params:
            url = url.format(**self.path_params)
        kwargs['headers'] = kwargs.get('headers', self.headers)
        kwargs['data'] = kwargs.get('data', self.data)
        kwargs['params'] = kwargs.get('params', self.params)
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        kwargs['proxies'] = kwargs.get('timeout', self.proxies)
        logging.info('kwargs={}'.format(kwargs))
        response = self.session.post(url, **kwargs)
        self.resp = Resp(response, self)
        return self.resp

    @step
    def put(self, url='', **kwargs):
        """
        发送 put 请求
        """
        if '://' not in url:
            url = urljoin(self.base_url, url)
        if self.path_params:
            url = url.format(**self.path_params)
        kwargs['headers'] = kwargs.get('headers', self.headers)
        kwargs['data'] = kwargs.get('data', self.data)
        kwargs['json'] = kwargs.get('json', self.json)
        kwargs['files'] = kwargs.get('files', self.files)
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        kwargs['proxies'] = kwargs.get('timeout', self.proxies)
        response = self.session.put(url, **kwargs)
        self.resp = Resp(response, self)
        return self.resp

    @step
    def delete(self, url='', **kwargs):
        """
        发送 delete 请求
        """
        if '://' not in url:
            url = urljoin(self.base_url, url)
        if self.path_params:
            url = url.format(**self.path_params)
        kwargs['headers'] = kwargs.get('headers', self.headers)
        kwargs['data'] = kwargs.get('data', self.data)
        kwargs['json'] = kwargs.get('json', self.json)
        kwargs['files'] = kwargs.get('files', self.files)
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)
        kwargs['proxies'] = kwargs.get('timeout', self.proxies)
        response = self.session.delete(url, **kwargs)
        self.resp = Resp(response, self)
        return self.resp


class Arrangement:
    def __init__(self, driver: HTTPDriver):
        self.driver = driver
        self.driver.params = dict()
        self.driver.data = dict()
        self.driver.json = ''
        self.driver.path_params = dict()
        self.driver.headers = dict()
        self.method = None

    @step
    def method(self, method):
        self.method = method
        return self

    @step
    def query_param(self, *parameters):
        for key, value in zip(*[iter(parameters)] * 2):
            self.driver.params[key] = value
        return self

    @step
    def form_param(self, *parameters):
        for key, value in zip(*[iter(parameters)] * 2):
            self.driver.data[key] = value
        return self

    @step
    def json(self, json_dict):
        self.driver.json = json_dict
        return self

    @step
    def path_param(self, *parameters):
        for key, value in zip(*[iter(parameters)] * 2):
            self.driver.path_params[key] = value
        return self

    @step
    def header_param(self, *parameters):
        for key, value in zip(*[iter(parameters)] * 2):
            self.driver.headers[key] = value
        return self

    @step
    def params(self, params):
        self.driver.params = params
        return self

    @step
    def data(self, data):
        self.driver.data = data
        return self

    @step
    def headers(self, headers):
        self.driver.headers = headers

    @step
    def cookies(self, cookies=None, cookie_dict=None, cookie_list=None):
        if cookie_list:
            cookie_dict = {item['name']: item['value'] for item in cookie_list}
        if cookie_dict:
            cookies = requests.utils.cookiejar_from_dict(cookie_dict, cookiejar=None, overwrite=True)
        self.driver.session.cookies = cookies
        return self

    @step
    def timeout(self, timeout):
        self.driver.timeout = timeout
        return self

    @step
    def action(self):
        return self.driver


class Resp:
    """
    响应内容类
    """
    def __init__(self, response, driver: HTTPDriver):
        self.response = response
        self.driver = driver
        self.session = driver.session
        self.extraction_obj: Extraction = None
        self.assertion_obj: Assertion = None

    @step('开始提取')
    def extraction(self):
        self.extraction_obj = Extraction(self)
        return self.extraction_obj

    @step('开始断言')
    def assertion(self):
        self.assertion_obj = Assertion(self)
        return self.assertion_obj

    def validation(self, yaml):
        pass


class Assertion:
    def __init__(self, resp: Resp):
        self.resp = resp
        self.response = resp.response

    @step
    @fail_to_log
    def status_code(self, assert_method):
        assert_method(self.response.status_code)
        return self

    @step
    @fail_to_log
    def json(self, assert_method, *key_or_kw):
        json = self.response.json()
        if not key_or_kw:
            assert_method(json)
        elif len(key_or_kw) == 1:
            key = key_or_kw[0]
            assert_method(json_parser(key, json))
        else:
            for key, value in zip(*[iter(key_or_kw)] * 2):
                assert_method(value)(json_parser(key, json))
        return self

    @step
    @fail_to_log
    def header(self, assert_method, *key_or_kw):
        headers = self.response.headers
        if not key_or_kw:
            assert_method(headers)
        elif len(key_or_kw) == 1:
            key = key_or_kw[0]
            assert_method(json_parser(key, headers))
        else:
            for key, value in zip(*[iter(key_or_kw)] * 2):
                assert_method(value)(json_parser(key, headers))
        return self

    @step
    @fail_to_log
    def url(self, assert_method):
        assert_method(self.response.url)
        return self

    @step
    @fail_to_log
    def encoding(self, assert_method):
        assert_method(self.response.encoding)
        return self

    @step
    @fail_to_log
    def content(self, assert_method):
        assert_method(self.response.content)
        return self

    @step
    @fail_to_log
    def text(self, assert_method):
        assert_method(self.response.text)
        return self

    @step
    @fail_to_log
    def history(self, assert_method):
        assert_method(self.response.history)
        return self

    def action(self):
        return self.resp


class Extraction:
    def __init__(self, resp: Resp):
        self.resp = resp
        self.response = resp.response

    @step
    @fail_to_log
    def status_code(self):
        return self.response.status_code

    @step
    @fail_to_log
    def json(self, key=None):
        json = self.response.json()
        if key:
            json = json_parser(key, json)
        return json

    @step
    @fail_to_log
    def raw(self):
        return self.response.raw

    @step
    @fail_to_log
    def header(self, key=None):
        headers = self.response.headers
        if key:
            headers = json_parser(key, headers)
        return headers

    @step
    @fail_to_log
    def url(self):
        return self.response.url

    @step
    @fail_to_log
    def encoding(self):
        return self.response.encoding

    @step
    @fail_to_log
    def content(self):
        return self.response.content

    @step
    @fail_to_log
    def text(self):
        return self.response.text

    @step
    @fail_to_log
    def history(self):
        return self.response.history


