import paramiko
import sys
import time
import requests
import connection

#Constants
host_ip="10.207.64.230"
user_name="root"
pwd="Password123!"
uemcli_file="UnisphereCLI-SUSE-Linux-64-x86-en_US-5.1.2.1501141-1.x86_64.rpm"

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


def uemcli_uninstall(ssh,version):
    print ("Currently uninstalling, please wait.....")
    uninstall_cmd = "rpm -e  UnisphereCLI-SUSE-Linux-64-x86-en_US-"+version.strip()+"-1.x86_64"
    stdin, stdout, stderr = ssh.exec_command(uninstall_cmd)
    output = stdout.readlines()
    version = uemcli_check(ssh)
    if (version):
        print ("Uninstallation failed. Please try uninstallation manually")
    else:
        print ("uninstallation successful")
    return

def uemcli_install(ssh):
    print("Currently installing, please wait.....")
    install_cmd="rpm -ivh /root/UnisphereCLI-SUSE-Linux-64-x86-en_US-5.1.2.1501141-1.x86_64.rpm"
    stdin, stdout, stderr = ssh.exec_command(install_cmd)
    output = stdout.readlines()
    version = uemcli_check(ssh)
    if (version):
        print("UEMCli installed and current UEMCLI version: ", version)
    else:
        print("uemcli installation failed...")

if __name__ == "__main__":

    ssh = connection.connectHost(host_ip,user_name,pwd)
    sftp = connection.transport(host_ip,user_name,pwd)
    target_path="/root/"+uemcli_file
    print (target_path)
    sftp.put(uemcli_file,target_path,confirm=True)
    ver_check_cmd = "uemcli -v"
    install_cmd = "rpm -ivh "+uemcli_file
    installed_ver = uemcli_check(ssh)
    if (installed_ver):
        print ("UEMCLI is already on this system. Version present is: ", installed_ver)
        option = input("Do you want to uninstall and Proceed with installation (y/n): ")
        if (option == 'y'):
            print ("uninstall older uemcli and will install newer version")
            uemcli_uninstall(ssh,installed_ver)
            uemcli_install(ssh)
        elif (option == 'n'):
            print ("Opted not to uninstall the uemcli. Hence stopping the script.")
    else:
        print ("uemcli not present. Proceeding to install uemcli")
        uemcli_install(ssh)

    sftp.close()
    ssh.close()