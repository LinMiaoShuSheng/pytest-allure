# -*- coding: utf-8 -*-
# !/usr/bin/env bash
"""
-------------------------------------------------
   File Name:     auto_test_client.py
   Description: need to pip below packages before use:
                  1、 pytest
                  2、allure-pytest
                  3、requests_toolbelt
-------------------------------------------------
"""
import subprocess
import os
import sys
import requests
import zipfile
import socket
import shutil
import getpass
import platform

from flask import Flask, redirect
from requests_toolbelt.multipart.encoder import MultipartEncoder

cur_path = os.path.abspath(sys.argv[0])
work_space = os.sep.join(cur_path.split(os.sep)[:-1])
sys.path.append(work_space)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

master_url_list = [
    # 因为当前lambda不支持动态多端口切换，因此暂时不使用lambda
    # "http://10.220.177.230:8100", "http://autotest.icitypainotebook.cbpmgt.com",  # for product
    "http://114.67.230.245:8100", "http://10.10.10.80:8100",  # for dev
    "http://116.196.93.180:8100", "http://10.10.10.23:8100"   # for test
]


def get_master():
    for url in master_url_list:
        command = "curl --connect-timeout 2 {}".format(url)
        code = subprocess.call(command, shell=True)
        if code != 0:
            continue
        else:
            return url + "/auto-test/allure/"
    return None


def get_report():
    print("work_space:{}".format(work_space))
    if platform.system().lower() == "linux":
        command = "cd {} && pytest --alluredir report > /dev/null".format(work_space)
    else:
        command = "cd {} && pytest --alluredir report > nul".format(work_space)
    print("the current test command is: {}".format(command))
    subprocess.call(command, shell=True)
    print("build report finished")


def zip_report(dir_path, out_full_name):
    """
    压缩指定文件夹
    :param dir_path: 目标文件夹路径
    :param out_full_name: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    print("the dir_path is: {}".format(dir_path))
    print("the out_full_name is: {}".format(out_full_name))

    if not os.path.exists(dir_path):
        print("no report file can be zipped")
        return

    zip = zipfile.ZipFile(out_full_name, "w", zipfile.ZIP_DEFLATED)
    for path, dir_names, filenames in os.walk(dir_path):
        file_path = path.replace(dir_path, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(file_path, filename))
    zip.close()
    print("zip {} finished".format(dir_path))


def get_allure_address(file_path, auto_test_master_url):
    print("get_allure_address start")
    file_data = MultipartEncoder(
        fields={'file': ('report.zip', open(file_path, 'rb'), 'multipart/form-data')}
    )

    host_name = socket.gethostname()  # 获取本机主机名
    user_name = getpass.getuser()  # 获取当前用户名
    # 个人存储位置以主机+用户+项目名作为唯一标识
    personal_dir = host_name + "_" + user_name + "_" + work_space.split(os.sep)[-1]
    print("personal_dir:{}".format(personal_dir))

    print("calling the url: {}".format(auto_test_master_url + personal_dir))

    response = requests.post(auto_test_master_url + personal_dir, data=file_data,
                             headers={'Content-Type': file_data.content_type})
    print("get the response:\n{}".format(response.text))
    response_dict = eval(response.text)
    allure_info = response_dict["data"]["allure_info"]
    print("get_allure_address finished: {}".format(allure_info))
    return allure_info


def del_file(path):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    print("template file {} cleaned".format(path))


@app.route('/')
def home_page():
    # 1、find a callable url for master
    auto_test_master_url = get_master()
    if not auto_test_master_url:
        message = "can't connect any auto_test_master node, " \
                  "please check whether auto_test_master crashed"
        return message

    # 2、get the test report
    get_report()

    # 3、zip report file
    dir_path = work_space + os.sep + "report"
    out_full_name = dir_path + ".zip"
    zip_report(dir_path=dir_path, out_full_name=out_full_name)

    # 4、get the allure address
    allure_address = get_allure_address(out_full_name, auto_test_master_url)

    # 5、remove the template files
    del_file(dir_path)
    del_file(out_full_name)

    return redirect(allure_address, code=302)


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(host='0.0.0.0', port=8848)
