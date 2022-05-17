import paramiko
from paramiko.ssh_exception import BadHostKeyException

def connectHost(host, user, pwd):
    print("Please Wait!!!!!. Establishing session to the host: ", host)
    try:
        session = paramiko.SSHClient()
        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        session.connect(host, username=user, password=pwd)
        return (session)
    except paramiko.ssh_exception.AuthenticationException:
        print("Authentication failed, please verify your credentials provided for the host: ", host)
        #return
        exit()
    except paramiko.ssh_exception.SSHException:
        print("Unable to establish SSH connection. Please re-check connectivity and try again on host: ", host)
        exit()
        #return
    except:
        print("Error occured in connecting to the host. Please re-verify manual connection and try again on host: ",
              host)
        exit()
        #return



def transport(server,user,pwd):
    transport = paramiko.Transport(server, 22)  # Create a transport Object
    transport.connect(username=user, password=pwd)  # Connect to transport Server
    sftp = paramiko.SFTPClient.from_transport(transport)  # Create an SFTP client
    return (sftp)