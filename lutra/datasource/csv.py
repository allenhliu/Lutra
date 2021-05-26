import csv
from functools import wraps
import pytest


def mds_csv(file):
    """
    mds_csv 用于装饰 fixture
    :param file:
    :return:
    """
    with open(file, 'r') as f:
        reader = csv.reader(f)
        fieldnames = next(reader)
        reader = csv.DictReader(f, fieldnames=fieldnames)
        params = list(reader)

    def decorate(func):
        @pytest.fixture(scope="module")
        @wraps(func)
        def wrapper(*args, **kwargs):
            # func 为测试用例
            result = func(*args, **kwargs, params=params)
            return result
        return wrapper
    return decorate


def ds_csv(file):
    """
    ds_csv 用于装饰 api
    :param file:
    :return:
    """
    with open(file, 'r') as f:
        reader = csv.reader(f)
        fieldnames = next(reader)
        reader = csv.DictReader(f, fieldnames=fieldnames)
        data = next(reader)

    def decorate(api):
        @wraps(api)
        def wrapper(*args, **kwargs):
            # func 为测试用例
            result = api(*args, **kwargs, data=data)
            return result
        return wrapper
    return decorate
