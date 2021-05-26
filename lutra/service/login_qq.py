# coding:utf-8
from lutra.driver.selenium import UIDriver
from lutra.page.qqlogin_page import QQLoginPage


class LoginService:
    @staticmethod
    def login(http_driver, uid, password, browser='Chrome'):
        ui_driver = UIDriver(browser)
        QQLoginPage.login(ui_driver, uid, password)
        cookies = ui_driver.get_cookies()
        ui_driver.clean()
        http_driver.set(cookies=cookies)
