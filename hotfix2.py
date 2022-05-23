import paramiko
import sys
import time
import requests
import connection
import apicall

sys.stdout.flush()

#Constants
SLES_VM=sys.argv[1]
user_name=sys.argv[2]
pwd=sys.argv[3]
build_num=sys.argv[4]
build_option=sys.argv[5]
os_user='c4dev'
os_pwd='c4dev!'
# sles12='10.207.128.32'
# sles15='10.244.32.23'
# build_num='5.1.3.0.5.003'

def checkHotfixFolder(sftp,folders_list):
    if "hotfix" not in folders_list:
        print("/home/c4dev/hotfix doesn't exist. Hence creating /home/c4dev/hotfix directory.......... ")
        sys.stdout.flush()
        sftp.mkdir("/home/c4dev/hotfix")
    else:  #change to root before passing the rm command
        print ("/home/c4dev/hotfix already existing. Deleting it for a neat operation....")
        sys.stdout.flush()
        sendInput(channel,"sudo su - \n",30)
        sendInput(channel,"rm -rf /home/c4dev/hotfix\n",180)
        sendInput(channel,"exit \n",10)
        print("creating /home/c4dev/hotfix directory.......... ")
        sys.stdout.flush()
        sftp.mkdir("/home/c4dev/hotfix")

def sendInput(channel,input,secs):
    print ("Command processed by sendInput function: ", input)
    sys.stdout.flush()
    channel.send(input)
    time.sleep(secs)
    return

def gethostname(ssh,cmd):
    stdin,stdout,stderr = ssh.exec_command(cmd)
    hostlist=stdout.readlines()
    for item in hostlist:
        hostname = item
    return(hostname.strip())

def sendCreds(channel,input,secs):
    channel.send(input)
    channel.send('\n')
    time.sleep(secs)
    return

def cleanUnityFolder(channel,secs):
    print("Cloned folder unity already present in /home/c4dev/hotfix. Deleting it for a neat clone...")
    sys.stdout.flush()
    channel.send("rm -rf unity\n")
    time.sleep(60)

def passCreds(channel,buf_data):

    if (buf_data.rstrip().endswith("Username for 'https://eos2git.cec.lab.emc.com':")):
        print("Providing username for eos2git section")
        sys.stdout.flush()
        sendCreds(channel, user_name, 5)
        return

    password_stmt1 = "Password for \'https://" + user_name + "@eos2git.cec.lab.emc.com\':"
    password_stmt1 = password_stmt1.rstrip()

    if (buf_data.rstrip().endswith(password_stmt1)):
        print("password provided for eos2git")
        sys.stdout.flush()
        sendCreds(channel,pwd,10)
        return

    if (buf_data.rstrip().endswith("Username for 'https://amaas-mr-mw1.cec.lab.emc.com':")):
        print("username provided for amaas: \n")
        sys.stdout.flush()
        sendCreds(channel, user_name, 5)
        return

    password_stmt2 = "Password for \'https://" + user_name + "@amaas-mr-mw1.cec.lab.emc.com\':"
    password_stmt2 = password_stmt2.rstrip()

    if (buf_data.rstrip().endswith(password_stmt2)):
        print("password provided for amaas...\n")
        sys.stdout.flush()
        sendCreds(channel, pwd, 15)
        return

def cloneUnity(channel,hostname):
    print("Cloning unity folder.....")
    sys.stdout.flush()
    buf_data = ' '
    git_clone_cmd = "git-lfs clone https://eos2git.cec.lab.emc.com/PIE/unity \n"
    sendInput(channel, git_clone_cmd, 30)

    prompt = "c4dev@" + hostname + ":~/hotfix>"
    while True:
        buf_data = channel.recv(9999).decode("utf-8")
        print ("#######################################")
        print (buf_data)
        sys.stdout.flush()

        if "git clone failed: exit status 128" in buf_data.rstrip():
            print ("Clone failed with exit status 128")
            sys.stdout.flush()
            break

        if "Git LFS " in buf_data.rstrip(): #size might change here.. as it is not constant all the time.
            print ("git-lfs clone completed")
            sys.stdout.flush()
            break

        if "Username for" in buf_data or "Password for" in buf_data:
            passCreds(channel,buf_data)
            continue

        elif prompt in buf_data:
            print ("Git-lfs clone completed")
            sys.stdout.flush()
            break
            
        else:
            time.sleep(10)
            continue

def git_checkout(channel, parent_id):
    cdCMD = "cd /home/c4dev/hotfix/unity\n"
    sendInput(channel, cdCMD, 10)
    buf_data= ' '
    cmd = "git checkout " + parent_id + " \n"
    sendInput(channel,cmd,10)

    while True:
        buf_data = channel.recv(9999).decode("utf-8")
        print(buf_data)
        sys.stdout.flush()

        if ("HEAD is now at ") in buf_data.rstrip():
            print ("git checkout completed...")
            sys.stdout.flush()
            break
        else:
            time.sleep(5)
            continue


def setExports(channel):

    cmd_list = ['export CFG_PREPARE_EMC_ARTIFACTS=0 \n',
                'export CFG_DISTRIBUTE_TYPE=HOTFIX \n',
                'export CFG_SIGN_TIMEOUT=2400 \n']

    for cmd in cmd_list:
        sendInput(channel,cmd,20)
        buf_data = channel.recv(9999).decode("utf-8")

    return

def hotfixBuild(channel, option):

    try:

        if (option == '1'):
            print ("Triggering hotfix build for GNOSIS_RETAIL. Build iteration number used is 222")
            sys.stdout.flush()
            GNOSIS_cmd = "nohup build/build_all -c -t GNOSIS_RETAIL --bvi 0 --build-iterator 222 & \n"

            sendInput(channel,GNOSIS_cmd, 10)
            sendInput(channel,"pwd \n",10)
            buf_data = channel.recv(9999).decode("utf-8")
            print(buf_data)
            sys.stdout.flush()

        elif (option == '2'):
            print ("Triggering hotfix build for VVNX_BIN_RETAIL")
            sys.stdout.flush()
            VVNX_cmd = "nohup build/build_all =t VVNX_BIN_RETAIL --bvi 0 --build-iterator 222 & \n"
            sendInput(channel, VVNX_cmd, 10)
            sendInput(channel, "pwd \n", 10)
            buf_data = channel.recv(9999).decode("utf-8")
            print(buf_data)
            sys.stdout.flush()

        print ("Please check the build generation status in the path: /home/c4dev/hotfix/unity/nohup.out")
        sys.stdout.flush()
        return

    except Exception:
        print ("Hotfix build creation failed: \n", Exception)
        sys.stdout.flush()
        return

if __name__ == "__main__":

    parent_id = apicall.getParentid(build_num)
    print("Parent Transaction ID for build " + build_num + " : " + parent_id)
    sys.stdout.flush()

    ssh = connection.connectHost(SLES_VM,os_user,os_pwd)
    channel = ssh.invoke_shell()
    host = gethostname(ssh,"hostname")

    sftp=connection.transport(SLES_VM, os_user,os_pwd)
    folders_list = sftp.listdir('/home/c4dev')

    checkHotfixFolder(sftp,folders_list)
    print ("copying env.config into /home/c4dev/hotfix folder..........")
    sys.stdout.flush()
    sftp.put('C:\\Users\\Administrator\\PycharmProjects\\unity\\env.config','/home/c4dev/hotfix/env.config',confirm=True,) #this can be used only to copy from local path to remote path

    while True:
        if channel.recv_ready():
            print ("*****Channel is ready*****")
            sys.stdout.flush()
            sendInput(channel,"cd /home/c4dev/hotfix\n",5)

            print ("performing dos2unix conversion for env.config........")
            sys.stdout.flush()
            sendInput(channel,"dos2unix env.config\n",5)

            print ("Setting +x permissions to env.config file")
            sys.stdout.flush()
            sendInput(channel,"chmod 777 env.config\n",5)

            print ("Enable git credential.helper Store")
            sys.stdout.flush()
            sendInput(channel,"git config --global credential.helper store\n",5)

            print ("Configuring environment by running env.config file")
            sys.stdout.flush()
            sendInput(channel,"sh env.config\n",5)

            recv_buf = channel.recv(9999).decode("utf-8")
            if recv_buf.endswith("Please input your password ->"):
                 sendCreds(channel,pwd.strip(),5)

            print ("Disabling git ssl verifying...")
            sys.stdout.flush()
            sendInput(channel,"git config --global http.sslverify false\n",5)
            recv_buf = channel.recv(9999).decode("utf-8")

            print ("Cloning git unity folder \n")
            sys.stdout.flush()
            cloneUnity(channel,host)

            print ("Checking out the parent_id: " + parent_id + "\n")
            sys.stdout.flush()
            git_checkout(channel,parent_id)

            print ("Setting the export parameters:")
            sys.stdout.flush()
            setExports(channel)

            if sys.argv[5] == "GNOSIS_RETAIL":
                print ("Triggering hotfix build for:", sys.argv[5])
                sys.stdout.flush()
                hotfixBuild(channel, "1")
            elif sys.argv[5] == "VVNX_BIN_RETAIL":
                print ("Triggering hotfix build for:", sys.argv[5])
                sys.stdout.flush()
                hotfixBuild(channel, "2")
            break
        else:
            time.sleep(20)
            print ("channel is not ready... please wait...")
            sys.stdout.flush()
            continue

    sftp.close()
    ssh.close()


