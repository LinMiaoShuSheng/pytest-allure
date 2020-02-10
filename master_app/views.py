# -*- coding: utf-8 -*-
# !/usr/bin/env bash
"""
-------------------------------------------------
   File Name:     views.py
   Description:   need to pip below packages before use:
                  1、 allure == 2.7.0 download for git
-------------------------------------------------
"""

from master_app.utils import *

env_init_ins = EnvVarsInit.get_instance()


# Create your views here.
def home_page(request):
    return HttpResponse(u"auto test master service already started")


def get_allure(request, personal_dir):
    """
        1、receive the zip file and unzip it
        2、find the free port
        3、start the allure
    """
    # 1、receive the zip file and unzip it
    file = request.FILES.get('file')

    print("the current zip file is {}".format(file.name))

    if file and allowed_file(file.name):
        file_name = file.name
        save_path, save_path_dir = get_save_path(personal_dir, file_name)

        with open(save_path, "wb") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        print("write down the file success")

        compress_dir = un_zip(save_path, save_path_dir)
        print("unzip finished, and the directory is {}".format(compress_dir))

    else:
        error_message = build_result_infos(data="no files uploaded", result="failed")
        return wrap_http_response(error_message)

    # 2、 get the free port
    host_ip = env_init_ins.host_ip
    port = get_port(host_ip)

    if not port:
        error_message = build_result_infos(data="no free port limit", result="failed")
        return wrap_http_response(error_message)

    # 3、start the allure
    thread_for_allure(port, compress_dir)

    allure_info = "http://{}:{}".format(host_ip, port)
    data = {"allure_info": allure_info}

    response_json = build_result_infos(data, "success")
    print("call get_allure finished, and the response_json is:{}".format(response_json))

    return wrap_http_response(response_json)
