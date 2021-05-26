# coding:utf-8
import time
import logging
import html
import pytest
from functools import wraps
from allure import step, severity_level

P0 = severity_level.BLOCKER
P1 = severity_level.CRITICAL
P2 = severity_level.NORMAL
P3 = severity_level.MINOR
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s')


def json_parser(key, json):
    for k in key.split('.'):
        k = int(k) if isinstance(json, list) else k
        json = json[k]
    return json


def html_unescape(s):
    return html.unescape(s)


def timestamp_13():
    return int(round(time.time())*1000)


class Assert:
    @staticmethod
    def bool(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
                logging.info('Converting assertion to boolean:')
                return True
            except AssertionError:
                return False
        return wrapper

    @staticmethod
    @step
    def nor(func):
        logging.info('Asserting not:')
        with pytest.raises(AssertionError):
            return func

    @staticmethod
    def be(value):
        @step
        def assert_y_is_x(y, x=value):
            logging.info('Asserting that {} is {}.'.format(y, x))
            assert y is x
        return assert_y_is_x

    @staticmethod
    def equal_to(value):
        @step
        def assert_y_equal_to_x(y, x=value):
            logging.info('Asserting that {} equal to {}.'.format(y, x))
            assert y == x
        return assert_y_equal_to_x

    @staticmethod
    def contain(*values):
        @step
        def assert_y_contain_xs(y, xs=values):
            for x in xs:
                logging.info('Asserting that {} equal to {}.'.format(y, x))
                assert x in y
        return assert_y_contain_xs

    @staticmethod
    def true():
        @step
        def assert_values_be_true(*values):
            logging.info('Asserting that {} are true.'.format(values))
            for y in values:
                assert y is True
        return assert_values_be_true

    @staticmethod
    def false():
        @step
        def assert_values_be_false(*values):
            logging.info('Asserting that {} are false.'.format(values))
            for value in values:
                assert value is False
        return assert_values_be_false

    @staticmethod
    def lt(value):
        @step
        def assert_y_lt_x(y, x=value):
            logging.info('Asserting that {} < {}.'.format(y, x))
            assert y < x
        return assert_y_lt_x

    @staticmethod
    def le(value):
        @step
        def assert_y_le_x(y, x=value):
            logging.info('Asserting that {} <= {}.'.format(y, x))
            assert y <= x
        return assert_y_le_x

    @staticmethod
    def gt(value):
        @step
        def assert_y_gt_x(y, x=value):
            logging.info('Asserting that {} > {}.'.format(y, x))
            assert y > x
        return assert_y_gt_x

    @staticmethod
    def ge(value):
        @step
        def assert_y_ge_x(y, x=value):
            logging.info('Asserting that {} >= {}.'.format(y, x))
            assert y >= x
        return assert_y_ge_x

    @staticmethod
    def ne(value):
        @step
        def assert_y_ne_x(y, x=value):
            logging.info('Asserting that {} != {}.'.format(y, x))
            assert y != x
        return assert_y_ne_x
