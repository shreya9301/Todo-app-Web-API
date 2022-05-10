import os
import platform
import uuid
import psutil
import socket
import subprocess
import threading

from . import fsutils
from . import strutils

def get_worker_id(prefix=None):
    """Get a unique name for a worker. The name template is `{prefix}:{hostname}:{process-id}:{thread-id}`.

    In [32]: from fastutils import sysutils

    In [33]: sysutils.get_worker_id('testapp')
    Out[33]: 'testapp:DESKTOP-MO5DJHQ:1896:9192'
    """
    worker_inner_id = "{}:{}:{}".format(socket.gethostname(), os.getpid(), threading.get_ident())
    if prefix:
        return prefix + ":" + worker_inner_id
    else:
        return worker_inner_id


def get_daemon_application_pid(pidfile):
    """Get pid from pidfile if the daemon process is alive. If the daemon process is dead, it will alway returns 0.
    """
    if os.path.exists(pidfile) and os.path.isfile(pidfile):
        with open(pidfile, "r", encoding="utf-8") as fobj:
            pid = int(fobj.read().strip())
        try:
            p = psutil.Process(pid=pid)
            return pid
        except psutil.NoSuchProcess:
            return 0
    else:
        return 0


def get_random_script_name():
    """Generate a random script name. For windows add .bat suffix.

    In [1]: import os

    In [2]: os.name
    Out[2]: 'nt'

    In [3]: from fastutils import sysutils

    In [4]: sysutils.get_random_script_name()
    Out[4]: '9b99d890-0b96-436d-9b1a-d70e9289e245.bat'
    """
    name = str(uuid.uuid4())
    if os.name == "nt":
        name += ".bat"
    return name

def execute_script(script, workspace=None, script_name=None):
    """Execute a shell script under special workspace.

    script: Script source code.
    workspace: Workspace path. If not given, a random template folder will be used.
    script_name: A name used for creating the temporary script file. If not given, a random name will be used.
    """
    workspace = workspace or fsutils.get_temp_workspace()
    if not os.path.exists(workspace):
        os.makedirs(workspace, exist_ok=True)
    
    script_name = script_name or get_random_script_name()
    script_path = os.path.join(workspace, script_name)
    fsutils.write(script_path, script)
    os.chmod(script_path, 0o755)

    p = subprocess.run(script_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workspace, shell=True, universal_newlines=True)
    code, stdout, stderr = p.returncode, p.stdout, p.stderr
    stdout = strutils.force_text(stdout)
    stderr = strutils.force_text(stderr)

    return code, stdout, stderr

def get_worker_info():
    """Get worker system information: hostname, system, release, version, machine, IPs, IPV4s, IPV6s, MACs.

    In [16]: from fastutils import sysutils

    In [17]: import json

    In [18]: print(json.dumps(sysutils.get_worker_info(), indent=4))
    {
        "hostname": "PC-MHOISDL",
        "system": "Windows",
        "release": "10",
        "version": "10.0.19042",
        "machine": "AMD64",
        "ips": [
            "192.168.1.123",
            "dd91::2355:3619:f34e:f54c"
        ],
        "ipv4s": [
            "192.168.1.123",
        ],
        "ipv6s": [
            "dd91::2355:3619:f34e:f54c"
        ],
        "macs": [
            "00-F3-C3-CF-19-24",
            "32-F9-DA-23-25-46",
        ]
    }
    """
    uname = platform.uname()
    ipv4s = set()
    ipv6s = set()
    macs = set()
    for _, iaddrs in psutil.net_if_addrs().items():
        for iaddr in iaddrs:
            if iaddr.family.name == "AF_LINK":
                macs.add(iaddr.address)
            elif iaddr.family.name == "AF_INET":
                ipv4s.add(iaddr.address)
            elif iaddr.family.name == "AF_INET6":
                ipv6s.add(iaddr.address)

    ipv4s.remove("127.0.0.1")
    ipv6s.remove("::1")

    ipv4s = list(ipv4s)
    ipv6s = list(ipv6s)
    macs = list(macs)
    ipv4s.sort()
    ipv6s.sort()
    macs.sort()

    return {
        "hostname": uname.node,
        "system": uname.system, 
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "ips": ipv4s + ipv6s,
        "ipv4s": ipv4s,
        "ipv6s": ipv6s,
        "macs": macs,
    }
