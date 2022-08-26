from __future__ import print_function
from asyncio.log import logger
import yaml
import time
import os
import subprocess
import logging
import time
import base64
import kubernetes.client
from kubernetes import config

env=os.getenv("ENV","dev")
default_connection_timeout = 60
def prerequisites():
    yaml_file = open(f"settings-{env}.yaml", 'r')
    settings = yaml.safe_load(yaml_file)
    return settings

##########################LOGGING##############################################
# https://docs.python.org/3/howto/logging.html#configuring-logging
# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create console handler and set level to INFO
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

def initiate_smb():
    try:
        subprocess.run(["sh","./connect.sh"])
    except Exception as e:
        logger.info(e)
    
def validate_db_details(db_details):
    
    # Check db_name key exists or not
    # Check if it is empty
    if ('db_name' not in db_details) or (len(str(db_details['db_name']))==0):
        logger.error("DB name not provided")
        return False
    return True

def mssql_database(db_details):
    try:
        
        logger.info(f"Starting Backup Of {db_details['db_name']} {db_details['env']}")
        # time1=time.strftime("%Y%m%d%H%M%S")
        subprocess.run(
                [ 
                    'sqlpackage',
                    '/a:export',
                    f'/ssn:{db_details["db_host"]}',
                    f'/st:{default_connection_timeout}',
                    f'/sdn:{db_details["db_name"]}',
                    f'/su:{db_details["db_user"]}',
                    f'/sp:{get_secrets(db_details["db_password"])}',
                    f'/tf:{db_details["backup_path"]}{db_details["db_name"]}_{db_details["env"]}.bacpac'
                    # f'/tf:{db_details["backup_path"]}{db_details["db_name"]}_{db_details["env"]}_{time.strftime("%Y%m%d%H%M%S")}.bacpac'
                ], check=True
            )
        logger.info("++++++++++++++++++Backup Completed++++++++++++++++++")
    except Exception as e:
        logger.info("++++++++++++++++++Backup Failed+++++++++++++++++++++")
        logger.info(e)

def get_secrets(dbpassword):
    config.load_incluster_config()
    api_instance = kubernetes.client.CoreV1Api()
    try:
        # read_namespaced_secret is Method
        api_response = api_instance.read_namespaced_secret(dbpassword["secret"]["name"],dbpassword["namespace"]).data
        # api_response = api_instance.read_namespaced_secret("smb-password","dbdump").data
        #print(api_response)
        return base64.b64decode(api_response[dbpassword["secret"]["key"]]).decode("utf-8")
    except Exception as e:
        logger.error("Cannot fetch password from secret",e)
        raise e

def backup_database(db_details):
    try:
        os.environ['PGPASSWORD'] = get_secrets(db_details["db_password"])
        logger.info(f"Starting Backup Of {db_details['db_name']} {db_details['env']}")
        subprocess.run(
            [ 
                'pg_dump',
                '-h', db_details["db_host"],
                '-p', str(db_details["db_port"]),
                '-d', db_details["db_name"], 
                '-U', db_details["db_user"], 
                '-Fc', '-v', 
                '-f', os.path.join(db_details["backup_path"],db_details["db_name"]+db_details["env"] + ".dump")
                # '-f', os.path.join(db_details["backup_path"],db_details["db_name"]+db_details["env"]+time.strftime("%Y%m%d%H%M%S") + ".dump")
            ], check=True
        )  

        logger.info("++++++++++++++++++++++++++++++++++++Backup Completed++++++++++++++++++++++++++++++++++++")
    except Exception as e:
        logger.info (e)
        logger.info ("++++++++++++++++++++++++++++++++++++Backup Failed+++++++++++++++++++++++++++++++++++++++")
        # logger.error(e)
        logger.error(e)

if __name__ == "__main__":
    settings=prerequisites()
    initiate_smb()
    for db in settings['DBs']:
        if not validate_db_details(db):
            logger.error("Incorrect DB details")
            continue
        if db["db_type"]=="pgsql":
            backup_database(db)
        elif db["db_type"]=="mssql":
            mssql_database(db)
        else:
            logger.error(f"Backup of {db['db_type']} type is not supported")
