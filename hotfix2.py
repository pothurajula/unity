import paramiko
import sys
import time
import requests
import connection
import apicall

#Constants
user_name='v_pothurajula'
pwd='Gabbar123$'
sles12='10.207.128.32'
sles15='10.244.32.23'
build_num='5.1.3.0.5.003'
os_user='c4dev'
os_pwd='c4dev!'

def checkHotfixFolder(sftp,folders_list):
    if "hotfix" not in folders_list:
        print("/home/c4dev/hotfix doesn't exist. Hence creating /home/c4dev/hotfix directory.......... ")
        sftp.mkdir("/home/c4dev/hotfix")
    else:  #change to root before passing the rm command
        print ("/home/c4dev/hotfix already existing. Deleting it for a neat operation....")
        sendInput(channel,"sudo su - \n",30)
        sendInput(channel,"rm -rf /home/c4dev/hotfix\n",180)
        sendInput(channel,"exit \n",10)
        print("creating /home/c4dev/hotfix directory.......... ")
        sftp.mkdir("/home/c4dev/hotfix")

def sendInput(channel,input,secs):
    print ("Command processed by sendInput function: ", input)
    channel.send(input)
    time.sleep(secs)
    return

def sendCreds(channel,input,secs):
    channel.send(input)
    channel.send('\n')
    time.sleep(secs)
    return

def cleanUnityFolder(channel,secs):
    print("Cloned folder unity already present in /home/c4dev/hotfix. Deleting it for a neat clone...")
    channel.send("rm -rf unity\n")
    time.sleep(60)

def passCreds(channel,buf_data):

    if (buf_data.rstrip().endswith("Username for 'https://eos2git.cec.lab.emc.com':")):
        print("Providing username for eos2git section")
        sendCreds(channel, user_name, 5)
        return

    password_stmt1 = "Password for \'https://" + user_name + "@eos2git.cec.lab.emc.com\':"
    password_stmt1 = password_stmt1.rstrip()

    if (buf_data.rstrip().endswith(password_stmt1)):
        print("password provided for eos2git")
        sendCreds(channel,pwd,10)
        return

    if (buf_data.rstrip().endswith("Username for 'https://amaas-mr-mw1.cec.lab.emc.com':")):
        print("username provided for amaas: \n")
        sendCreds(channel, user_name, 5)
        return

    password_stmt2 = "Password for \'https://" + user_name + "@amaas-mr-mw1.cec.lab.emc.com\':"
    password_stmt2 = password_stmt2.rstrip()

    if (buf_data.rstrip().endswith(password_stmt2)):
        print("password provided for amaas...\n")
        sendCreds(channel, pwd, 15)
        return

def cloneUnity(channel):
    print("Cloning unity folder.....")
    buf_data = ' '
    git_clone_cmd = "git-lfs clone https://eos2git.cec.lab.emc.com/PIE/unity \n"
    sendInput(channel, git_clone_cmd, 30)

    while True:
        buf_data = channel.recv(9999).decode("utf-8")
        print ("#######################################")
        print (buf_data)

        if "git clone failed: exit status 128" in buf_data.rstrip():
            print ("Clone failed with exit status 128")
            break

        if "Git LFS " in buf_data.rstrip(): #size might change here.. as it is not constant all the time.
            print ("git-lfs clone completed")
            break

        elif "Username for" in buf_data or "Password for" in buf_data:
            passCreds(channel,buf_data)
            continue

        else:
            time.sleep(10)
            continue
    return

def git_checkout(channel, parent_id):
    cdCMD = "cd /home/c4dev/hotfix/unity\n"
    sendInput(channel, cdCMD, 10)
    buf_data= ' '
    cmd = "git checkout " + parent_id + " \n"
    sendInput(channel,cmd,10)

    while True:
        buf_data = channel.recv(9999).decode("utf-8")
        print(buf_data)

        if ("HEAD is now at ") in buf_data.rstrip():
            print ("git checkout completed...")
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
            GNOSIS_cmd = "nohup build/build_all -c -t GNOSIS_RETAIL --bvi 0 --build-iterator 222 & \n"

            sendInput(channel,GNOSIS_cmd, 10)
            sendInput(channel,"pwd \n",10)
            buf_data = channel.recv(9999).decode("utf-8")
            print(buf_data)

        elif (option == '2'):
            print ("Triggering hotfix build for VVNX_BIN_RETAIL")
            VVNX_cmd = "nohup build/build_all =t VVNX_BIN_RETAIL --bvi 0 --build-iterator 222 & \n"
            sendInput(channel, VVNX_cmd, 10)
            sendInput(channel, "pwd \n", 10)
            buf_data = channel.recv(9999).decode("utf-8")
            print(buf_data)

        print ("Please check the build generation status in the path: /home/c4dev/hotfix/unity/nohup.out")
        return

    except Exception:
        print ("Hotfix build creation failed: \n", Exception)
        return

if __name__ == "__main__":

    parent_id = apicall.getParentid(build_num)
    print("Parent Transaction ID for build " + build_num + " : " + parent_id)

    ssh = connection.connectHost(sles15,os_user,os_pwd)
    channel = ssh.invoke_shell()

    sftp=connection.transport(sles15, os_user,os_pwd)
    folders_list = sftp.listdir('/home/c4dev')

    checkHotfixFolder(sftp,folders_list)
    print ("copying env.config into /home/c4dev/hotfix folder..........")
    sftp.put('env.config','/home/c4dev/hotfix/env.config',confirm=True,) #this can be used only to copy from local path to remote path

    while True:
        if channel.recv_ready():
            print ("*****Channel is ready*****")
            sendInput(channel,"cd /home/c4dev/hotfix\n",5)

            print ("performing dos2unix conversion for env.config........")
            sendInput(channel,"dos2unix env.config\n",5)

            print ("Setting +x permissions to env.config file")
            sendInput(channel,"chmod 777 env.config\n",5)

            print ("Enable git credential.helper Store")
            sendInput(channel,"git config --global credential.helper store\n",5)

            print ("Configuring environment by running env.config file")
            sendInput(channel,"sh env.config\n",5)

            recv_buf = channel.recv(9999).decode("utf-8")
            if recv_buf.endswith("Please input your password ->"):
                 sendCreds(channel,pwd.strip(),5)

            print ("Disabling git ssl verifying...")
            sendInput(channel,"git config --global http.sslverify false\n",5)
            recv_buf = channel.recv(9999).decode("utf-8")

            print ("Cloning git unity folder \n")
            cloneUnity(channel)

            print ("Checking out the parent_id: " + parent_id + "\n")
            git_checkout(channel,parent_id)

            print ("Setting the export parameters:")
            setExports(channel)

            print("Choose from below options to trigger hotfix build: \n"
                        "1: GNOSIS_RETAIL \n"
                        "2: VVNX_BIN_RETAIL")
            option = input("Key-in the input: ")
            hotfixBuild(channel, option)

            break
        else:
            time.sleep(20)
            print ("channel is not ready... please wait...")
            continue

    sftp.close()
    ssh.close()


