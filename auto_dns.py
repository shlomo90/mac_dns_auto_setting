import subprocess
from lxml import etree
from daemon import daemon
from time import sleep


DELAY = 10

class AutoDNS(daemon):
    AP_DNS_MAP = {
        'default': ['8.8.4.4'],
    }

    def run(self):
        while True:
            sleep(DELAY)
            self._run()

    def _set_dns_server(self, ips):
        cmd = 'networksetup -setdnsservers Wi-Fi {}'
        os.system(cmd.format(' '.join(ips)))

    def _get_dns_server(self):
        cmd = 'networksetup -getdnsservers Wi-Fi'
        server_ips = []
        for ip in subprocess.check_output(cmd, shell=True).split('\n'):
            server_ips.append(ip.strip())
        return server_ips

    def _run(self):
        cmd = (
            '/System/Library/PrivateFrameworks/Apple80211.framework/'
            'Versions/Current/Resources/airport /usr/sbin/airport -I'
        )

        ap_name = None
        for line in subprocess.check_output(cmd, shell=True).split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('SSID: '):
                ap_name = line_stripped[6:]
                break

        if ap_name in self.AP_DNS_MAP:
            dns_ip = self.AP_DNS_MAP.get(ap_name)
            if set(dns_ip).intersection(set(self._get_dns_server())):
                return
            else:
                self._set_dns_server(dns_ip)
        else:
            dns_ip = self.AP_DNS_MAP['default']
            self._set_dns_server(dns_ip)
