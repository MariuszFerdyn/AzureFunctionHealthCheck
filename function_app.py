# Install required packages if not present
import subprocess
import sys

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = ['azure-functions', 'PyYAML', 'requests']
for package in required_packages:
    try:
        __import__(package.replace('-', '.'))
    except ImportError:
        print(f"Installing {package}...")
        install_package(package)

# Your original imports
import azure.functions as func
import datetime
import json
import logging
import yaml
import ipaddress
import urllib.parse
import socket
import requests
import re
import logging
import logging.handlers
import random
import string
import hashlib
import os
import time
import platform

log_dest = 'console'
logger = None
default_config_url = ''
args = {
    'some_key': 'some_value',
    # Add other necessary key-value pairs
}

app = func.FunctionApp()

def checksum(filename, hashfunc):
    with open(filename,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            hashfunc.update(byte_block)
    return hashfunc.hexdigest()

def log(log, end='\n', flush=True):
    if log_dest == 'file' or log_dest == 'syslog':
        logger.info(log)
    elif log_dest == 'none':
        pass
    elif log_dest == 'azurefunction':
        logging.info(log)
    else:
        print(log, end=end, flush=flush)

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=False) 
def HealtchCheck01(myTimer: func.TimerRequest) -> None:

  
    if myTimer.past_due:
        logging.info('The timer is past due!')

##################
    global log_dest
    global logger
    future_log = ''

    retcode = 0
    config = None

    SSLVerify = False
    logging.captureWarnings(True)
    
    # Fix: Convert args dictionary values to a list and combine with other config sources
    config_sources = list(args.values()) + [default_config_url, os.path.dirname(__file__) + '/config.yml']

    for f in config_sources:
        url = urllib.parse.urlparse(f,scheme='http')
        if url.netloc!='':
            try:
                r = requests.get(url.geturl(), verify=SSLVerify, timeout=5)
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                r = None
            if r is not None and r.ok:
                config = yaml.load(r.text, Loader=yaml.Loader)
                future_log += f'Loaded config from {url.geturl()}'
                break
        else:
            try:
                with open(f) as file:
                    config = yaml.load(file, Loader=yaml.Loader)
                    future_log += f'Loaded config from {f}'
                    break
            except OSError:
                pass

    if not config:
        logging.critical('invalid config')
        return -1

    try:
        log_dest = config['config']['log']
    except KeyError:
        log_dest = 'console'
    if log_dest == 'syslog':
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.handlers.SysLogHandler(address='/dev/log'))
    elif log_dest == 'file':
        try:
            logfile = config['config']['logfile']
        except KeyError:
            log_dest = 'console'
            logging.error('logfile not defined')
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(filename=logfile)
        hastname = platform.node()
        fh.setFormatter(logging.Formatter(f'%(asctime)s {platform.node()}: %(message)s'))
        logger.addHandler(fh)


    istty = log_dest == 'console' and sys.stdout.isatty()

    if istty: print(future_log)
    else: log(future_log)
    future_log = ''

    FAIL = "\033[1;91m" + "FAIL" + "\033[0m" if istty else "FAIL"
    PASS = "\033[1;92m" + "PASS" + "\033[0m" if istty else "PASS"

    try:
        loop_delay = config['config']['loop_delay'] + 1 - 1
    except (KeyError, TypeError):
        loop_delay = -1

    do_loop = True
    while do_loop:
     if loop_delay < 0 :
         do_loop = False
     else:
         time.sleep(loop_delay)

     for i in config['hosts']:
        try:
            addr = i['address']
            try:
                addr = str(ipaddress.ip_address(addr))
                url = urllib.parse.urlparse(f'http://{addr}')
            except ValueError:
                url = urllib.parse.urlparse(addr,scheme='http')
                if url.netloc=='' and url.path != '':
                    url = urllib.parse.urlparse(f'{url.scheme}://{url.path}')
                addr =  url.hostname
        except KeyError:
            continue

        if i['prot'] == 'icmp':
            msg_format = f'{i["prot"]:12}{addr:30}: ' if istty else f'{i["prot"]} {addr}: '
            if istty: print(msg_format, end='', flush=True)
            start = time.perf_counter()
            cp = subprocess.run(['ping','-c1','-w2',addr],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            end = time.perf_counter()
            PASS_TIME = PASS + f' {((end-start)*1000):.2f}ms '
            result = f'{FAIL if cp.returncode else PASS_TIME}'
            if istty: print(result)
            else: log(msg_format + result)
            retcode = retcode + cp.returncode
        elif i['prot'] == "tcp":
            i_prot = f'tcp/{i["tcpport"]}'
            msg_format = f'{i_prot:12}{addr:30}: ' if istty else f'{i_prot} {addr}: '
            if istty: print(msg_format, end='', flush=True)
            s = None
            for res in socket.getaddrinfo(addr, i['tcpport'], socket.AF_UNSPEC, socket.SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                try:
                    s = socket.socket(af, socktype, proto)
                    s.settimeout(5)
                except socket.error:
                    s = None
                    continue
                try:
                    start = time.perf_counter()
                    s.connect(sa)
                except socket.error:
                    s.close()
                    s = None
                    continue
                break
            end = time.perf_counter()
            PASS_TIME = PASS + f' {((end-start)*1000):.2f}ms '
            result = f'{PASS_TIME if s else FAIL}'
            if istty: print(result)
            else: log(msg_format + result)
            retcode = retcode + (0 if s else 1)
            if s: s.close()
        elif i['prot'] == 'httpstatus':
            addr = url.geturl()
            msg_format = f'{i["prot"]:12}{addr:30}: ' if istty else f'{i["prot"]} {addr}: '
            if istty: print(msg_format, end='', flush=True)
            start = time.perf_counter()
            try:
                r = requests.get(addr, verify=SSLVerify, timeout=5)
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                r = None
            end = time.perf_counter()
            PASS_TIME = PASS + f' {((end-start)*1000):.2f}ms '
            result = f'{PASS_TIME if r and r.status_code==i["httpstatus"] else FAIL}'
            if istty: print(result)
            else: log(msg_format + result)
            retcode = retcode + (0 if r and r.status_code==i["httpstatus"] else 1)
        elif i['prot'] == 'httpstring':
            addr = url.geturl()
            msg_format = f'{i["prot"]:12}{addr:30}: ' if istty else f'{i["prot"]} {addr}: '
            if istty: print(msg_format, end='', flush=True)
            start = time.perf_counter()
            try:
                r = requests.get(addr, verify=SSLVerify, timeout=5)
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                r = None
            end = time.perf_counter()
            PASS_TIME = PASS + f' {((end-start)*1000):.2f}ms '
            result = f'{PASS_TIME if r and re.search(i["httpstring"],r.text) else FAIL}'
            if istty: print(result)
            else: log(msg_format + result)
            retcode = retcode + (0 if r and re.search(i["httpstring"],r.text) else 1)
        elif i['prot'] == 'icap':
            msg_format = f'{i["prot"]:12}{addr:30}: ' if istty else f'{i["prot"]} {addr}: '
            if istty: print(msg_format, end='', flush=True)
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            try:
                tmout = i['icaptimeout']
            except KeyError:
                tmout = 20
            for f in [ i["icaptestfile"], os.path.dirname(__file__)+"/"+i["icaptestfile"] ]:
                if os.path.isfile(f):
                    i['icaptestfile'] = f
                    break
            try:
                start = time.perf_counter()
                cp = subprocess.run(['c-icap-client','-i',addr,'-s',i["icapservice"],'-f',i["icaptestfile"],'-o',i["icaptestfile"]+suffix],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=tmout)
                end = time.perf_counter()
                PASS_TIME = PASS + f' {((end-start)*1000):.2f}ms '
            except subprocess.TimeoutExpired:
                cp.returncode = 1
            if cp.returncode == 0:
                if os.path.isfile(i['icaptestfile']+suffix):
                    c2 = checksum(i['icaptestfile']+suffix,hashlib.md5())
                    if checksum(i['icaptestfile'],hashlib.md5()) != c2:
                        if istty: print(PASS_TIME)
                        else: log(msg_format + PASS_TIME)
                        continue

            try:
                os.remove(i['icaptestfile']+suffix)
            except FileNotFoundError:
                pass
            if istty: print(FAIL)
            else: log(msg_format + FAIL)
            retcode += 1
            continue

    if retcode == 0:
        logging.info("Health check passed.")
    else:
        logging.error("Health check failed.")
    #return 0

##################

    logging.info('Python timer trigger function executed.')
