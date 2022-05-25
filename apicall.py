import requests

def getParentid(build_num):

    try:
        url = "http://ibid.usd.lab.emc.com/api/search?build_revision=%22" + build_num + "%22"
        response = requests.get(url)

        if (response.status_code == 200):
            url = ''.join((response.json()['results']))
            response2 = requests.get(url)
            parent_id = ''.join((response2.json()['parent_transaction_id']))
            if (parent_id):
                return parent_id
            else:
                print ("No parent id found. Stopping the script")
                exit(-1)
        else:
            print ("unable to reach ",url)
            print ("Hence exiting the script")
            exit(-1)

    except Exception:

        print ("Unable to get Parent Transaction ID. PLease check build number provided or build url once")
        exit(-1)
