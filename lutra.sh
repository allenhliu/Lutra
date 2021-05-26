#!/bin/bash
set -x
python -m pytest -p no:cacheprovider $@ --alluredir=xml_report
result=$?
allure generate xml_report -o report --clean && exit ${result}