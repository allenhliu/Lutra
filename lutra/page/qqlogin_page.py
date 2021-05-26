# coding:utf-8
from selenium.webdriver.common.by import By
from urllib.parse import urlencode
LOGIN_URL = 'https://xui.ptlogin2.qq.com/cgi-bin/xlogin?'
APP_ID = '636014201'
S_URL = 'https://www.qq.com'


class QQLoginPageElem:
    p_login = By.ID, 'switcher_plogin'
    u = By.ID, 'u'
    p = By.ID, 'p'
    submit = By.ID, 'login_button'
    qq_logged = By.ID, 'loginGrayIconLogin'


class QQLoginPage:
    @staticmethod
    def login(ui_driver, uid, password, appid=APP_ID, s_url=S_URL, login_url=LOGIN_URL,
              logged_locator=QQLoginPageElem.qq_logged):
        s_url = ui_driver.base_url or s_url
        url = login_url + urlencode(dict(appid=appid, s_url=s_url))
        d = ui_driver
        d.goto(url)
        d.find(QQLoginPageElem.p_login).click()
        d.find(QQLoginPageElem.u).clear().input(uid)
        d.find(QQLoginPageElem.p).clear().input(password)
        d.find(QQLoginPageElem.submit).click()
        d.find(logged_locator)
