import paramiko
import sys
import time
import requests
import connection
import sys
import os
#Constants
host=sys.argv[1]
user_name=sys.argv[2]
pwd=sys.argv[3]
array=sys.argv[4]
force_flag = sys.argv[5]
rpm=sys.argv[6]

def renamerpm():
    os.rename("UEMCLI_RPM",rpm)

def gethostname(ssh,cmd):
    stdin,stdout,stderr = ssh.exec_command(cmd)
    hostlist=stdout.readlines()
    for item in hostlist:
        hostname = item
        return(hostname.strip())

def uemcli_check(ssh):
    ver_check_cmd = "uemcli -v"
    stdin, stdout, stderr = ssh.exec_command(ver_check_cmd)
    output = stdout.readlines() #this returns a list.
    if not output: #checking if output is empty, if empty enters this if section
        return None
    else:
        dict1 = {}
        for line in output:
            [k, v] = line.split(':')
            dict1[k] = v
        if 'Version' in dict1.keys():
            return (dict1['Version'])
        else:
            print ("issue encountered. Please check output of uemcli -v and manually uninstall uemcli")
            sys.stdout.flush()

def uemcli_uninstall(ssh,version):
    print ("Currently uninstalling, please wait.....")
    sys.stdout.flush()
    uninstall_cmd = "rpm -e  UnisphereCLI-SUSE-Linux-64-x86-en_US-"+version.strip()+"-1.x86_64"
    stdin, stdout, stderr = ssh.exec_command(uninstall_cmd)
    output = stdout.readlines()
    version = uemcli_check(ssh)
    if (version):
        print ("Uninstallation failed. Please try uninstallation manually")
        sys.stdout.flush()
    else:
        print ("uninstallation successful")
        sys.stdout.flush()
    return

def uemcli_install(ssh,target_path):
    print("Currently installing, please wait.....")
    sys.stdout.flush()
    install_cmd="rpm -ivh "+target_path
    stdin, stdout, stderr = ssh.exec_command(install_cmd)
    output = stdout.readlines()
    version = uemcli_check(ssh)
    if (version):
        print("UEMCli installed and current UEMCLI version: ", version)
        sys.stdout.flush()
    else:
        print("uemcli installation failed...")
        sys.stdout.flush()

def connection_check(ssh,host):
    print ("Verifying uemcli connection to array by running an healthcheck onto array: ",array)
    sys.stdout.flush()
    prompt = host + ":~ #"
    uemcli_cmd="uemcli -d "+array+" -u admin -p Password123! /sys/general healthcheck"
    recv_buf = ''
    channel=ssh.invoke_shell()
    channel.send(uemcli_cmd + "\n")
    time.sleep(5)
    while True:
        if channel.recv_ready():
            print ("Channel is ready")
            sys.stdout.flush()
            while True:
                recv_buf= channel.recv(9999).decode("utf-8")
                print (recv_buf)
                sys.stdout.flush()

                if "Please input your selection (The default selection is [1]):" in recv_buf.rstrip():
                    option = "3"
                    channel.send(option)
                    channel.send("\n")

                if "Operation completed successfully." in recv_buf.rstrip():
                    print ("UEMCLI connection check completed.")
                    sys.stdout.flush()
                    return

                elif prompt in recv_buf[-30:]:
                    print ("Couldn't connect to the array")
                    sys.stdout.flush()
                    exit()

                else:
                    time.sleep(10)
                    recv_buf=''
                    continue
        else:
            time.sleep(10)
            print ("Channel is not ready.. wait for channel to be ready")
            sys.stdout.flush()
            continue

if __name__ == "__main__":

    ssh = connection.connectHost(host,user_name,pwd)
    sftp = connection.transport(host,user_name,pwd)
    renamerpm()
    target_path="/root/Desktop/"+rpm
    print ("Copying uemcli rpm in path ",target_path)
    sys.stdout.flush()
    #print (target_path)
    host=gethostname(ssh,"hostname")
    sftp.put(rpm,target_path,confirm=True)
    ver_check_cmd = "uemcli -v"
    install_cmd = "rpm -ivh "+rpm
    installed_ver = uemcli_check(ssh)
    if (installed_ver):
        print ("UEMCLI is already on this system. Version present is: ", installed_ver)
        sys.stdout.flush()
        if (force_flag == 'Yes'):
            print ("uninstall older uemcli and will install newer version")
            sys.stdout.flush()
            uemcli_uninstall(ssh,installed_ver)
            uemcli_install(ssh,target_path)
        elif (force_flag == 'No'):
            print ("Opted not to uninstall the uemcli. Hence stopping the script.")
            sys.stdout.flush()
            exit()
    else:
        print ("uemcli not present. Proceeding to install uemcli")
        sys.stdout.flush()
        uemcli_install(ssh,target_path)
    print("\n##############################")
    sys.stdout.flush()
    connection_check(ssh,host)
    print("##############################\n")
    sys.stdout.flush()
    sftp.close()
    ssh.close()