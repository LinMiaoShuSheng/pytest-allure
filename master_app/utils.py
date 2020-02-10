from configparser import ConfigParser
from multiprocessing import Lock
from django.http import HttpResponse
import os
import logging
import zipfile
import threading
import subprocess
import json
import datetime
import shutil

lock = Lock()

logging.Formatter(
    fmt='auto_test|%(asctime)s|%(levelname)s|%(funcName)s|%(filename)s:%(lineno)d|%(message)s')
logging.Formatter.default_msec_format = '%s.%03d'

ALLOWED_EXTENSIONS = set({"zip"})  # 允许文件上传的格式


class EnvVarsInit:
    __instance = None
    __instance_lock = threading.Lock()

    def __init__(self):
        self.config = ConfigParser()
        config_file = "configuration.ini"
        cur_file_path = os.path.dirname(os.path.realpath(__file__))

        configuration_file_path = os.sep.join(cur_file_path.split(os.sep)[:-1]) + os.sep + config_file
        print("the current configuration file path is:{}".format(configuration_file_path))
        self.config.read(configuration_file_path)

    @staticmethod
    def get_instance():
        if not EnvVarsInit.__instance:
            with EnvVarsInit.__instance_lock:
                if not EnvVarsInit.__instance:
                    EnvVarsInit.__instance = EnvVarsInit()
        return EnvVarsInit.__instance

    @property
    def host_ip(self):
        return self.config.get("host", "MASTER")

    @property
    def upload_file_dir(self):
        upload_file_dir = self.config.get("upload_file", "PATH").lower()
        upload_file_dir = upload_file_dir if upload_file_dir.endswith(os.sep) else upload_file_dir + os.sep
        return upload_file_dir


env_init_ins = EnvVarsInit.get_instance()


def allowed_file(filename):
    return '.' in filename and filename.split('.')[-1] in ALLOWED_EXTENSIONS


def del_file(path):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    print("template file {} cleaned".format(path))


def get_save_path(personal_dir, file_name):
    personal_dir = personal_dir[1:] if personal_dir.startswith(os.sep) else personal_dir
    print("personal_dir is {} ".format(personal_dir))

    upload_file_dir = env_init_ins.upload_file_dir
    print("upload_file_dir is {} ".format(upload_file_dir))

    save_path_dir = upload_file_dir + personal_dir
    save_path = save_path_dir + os.sep + file_name

    if os.path.exists(save_path_dir):
        del_file(save_path_dir)  # remove the history dir
    os.makedirs(save_path_dir)

    print("save_path is {} ".format(save_path))
    print("save_path_dir is {} ".format(save_path_dir))

    return save_path, save_path_dir


def un_zip(filename, save_path_dir):
    zip_file = zipfile.ZipFile(filename)
    print("the current compress_dir is {}".format(save_path_dir))
    if not os.path.exists(save_path_dir):
        print("going to create compress_dir ... ...")
        os.mkdir(save_path_dir)
    print("unpacking the zip file ... ...")
    for names in zip_file.namelist():
        print(names)
        zip_file.extract(names, save_path_dir)
    zip_file.close()
    return save_path_dir


def get_port(host_ip):
    for port in range(8100, 65535):
        if os.popen("netstat -na | grep {}".format(port)).readlines():
            print("{}:{} has already been used".format(host_ip, port))
            continue
        else:
            print("get a free port: {}".format(port))
            return port
    return None


def start_allure(port, report_dir):
    print("the current report dir is: {}".format(report_dir))
    command = "allure serve --host 0.0.0.0 --port {} {}".format(port, report_dir)
    print("going to start allure")
    print("the current command is: {}".format(command))
    code = subprocess.call(command, shell=True)
    result = "failed" if code != 0 else "success"
    print("allure server start {}".format(result))


def thread_for_allure(port, report_dir):
    thread = threading.Thread(target=start_allure,
                              kwargs={"port": port, "report_dir": report_dir})
    thread.start()


def build_result_infos(data=None, result="success"):
    response_json = {"code": 200, "message": result}
    if data is None:
        return response_json
    else:
        response_json.update({"data": data})
        return response_json


def wrap_http_response(response_json: dict):
    return HttpResponse(json.dumps(response_json, ensure_ascii=False, cls=MyJsonEncoder),
                        content_type="application/json,charset=utf-8")


class MyJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return json.JSONEncoder.default(self, obj)
