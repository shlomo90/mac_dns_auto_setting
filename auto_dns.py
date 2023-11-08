#-*- encoding:utf-8 -*-
"""
이 프로그램은 주기적으로 Network Wifi 를 읽고 특정 SSID 로 처음 변경되었을 때,
DNS 를 지정된 IP 로 변경해주는 기능이다.
"""

import os
import subprocess
from daemon import daemon
from time import sleep
from datetime import datetime


AP_DNS_MAP = {
    # SSID 에 대응되는 DNS IP 를 설정한다.
    # 아래는 'wifi' 라는 SSID 에 대해 8.8.8.8 을 설정하는 예시.
    'wifi': [
        '8.8.8.8',
    ]
}

# PID File Path
PIDFILE_PATH = '/var/tmp/auto_dns.pid'

# Checker Delay
DELAY = 10

# Debug Log option.
DEBUG = False


def check_output(cmd):
    # subprocess output is bytes encoded to utf-8. We need to decode it.
    ret = subprocess.check_output(cmd, shell=True).decode("utf-8")
    # the returned content of subprocess has escaped newlines.
    ret = ret.strip().replace('\\n', '\n')
    return ret


class Logger():
    def __init__(self):
        self.path = '/var/tmp/auto_dns.log'
        self.fobj = open(self.path, 'a+')

    def info(self, msg):
        now = datetime.now()
        self.fobj.write("{} [info]: {}\n".format(now, msg))
        self.fobj.flush()

    def error(self, msg):
        now = datetime.now()
        self.fobj.write("{} [error]: {}\n".format(now, msg))
        self.fobj.flush()

    def debug(self, msg):
        if DEBUG is True:
            now = datetime.now()
            self.fobj.write("{} [debug]: {}\n".format(now, msg))
            self.fobj.flush()


logger = Logger()


class AutoDNS(daemon):
    def run(self):
        while True:
            try:
                sleep(DELAY)
                logger.debug("Start AutoDNS")
                self._run()
                logger.debug("End AutoDNS")
            except Exception as e:
                logger.error("{}".format(e))

    def _set_dns_server(self, ips):
        cmd = 'networksetup -setdnsservers Wi-Fi {}'.format(' '.join(ips))
        os.system(cmd)
        logger.debug("cmd:{}".format(cmd))

    def _get_dns_server(self):
        cmd = 'networksetup -getdnsservers Wi-Fi'
        server_ips = []
        return_lines = check_output(cmd)
        for ip in return_lines.split('\n'):
            logger.debug("ip:{}".format(ip))
            server_ips.append(ip.strip())
        return server_ips

    def _get_current_ssid(self):
        cmd = (
            '/System/Library/PrivateFrameworks/Apple80211.framework/'
            'Versions/Current/Resources/airport /usr/sbin/airport -I'
        )

        ap_name = None
        return_lines = check_output(cmd)
        for line in return_lines.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('SSID: '):
                ap_name = line_stripped[6:]
                break
        return ap_name

    def _run(self):
        ap_name = self._get_current_ssid()
        logger.debug("ap_name:{}".format(ap_name))
        set_ips = AP_DNS_MAP.get(ap_name, [])
        logger.debug("set_ips:{}".format(set_ips))
        if set_ips:
            current_dns_ips = self._get_dns_server()
            for dns_ip in current_dns_ips:
                logger.debug("dns_ip:{}".format(dns_ip))
                if dns_ip in set_ips:
                    # No need to set dns ip.
                    return
            self._set_dns_server(set_ips)
            logger.info("DNS Server changed: old({}) -> new({})".format(
                ' '.join(current_dns_ips), ' '.join(set_ips)))


if __name__ == "__main__":
    daemon = AutoDNS(PIDFILE_PATH)
    daemon.start()
