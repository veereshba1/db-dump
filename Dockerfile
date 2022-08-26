FROM python:3.8

RUN apt-get update && apt-get install -y lsb-release && apt-get clean all 
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get update    
RUN apt-get -y install postgresql \
    cifs-utils 

WORKDIR dbDumpScript/

RUN wget https://aka.ms/sqlpackage-linux -O sqlpackage-linux
RUN unzip sqlpackage-linux -d /usr/bin
RUN chmod +x /usr/bin/sqlpackage

COPY dbdump.py requirements.txt settings*.yaml connect.sh ./

RUN pip install -r ./requirements.txt

CMD ["python","dbdump.py"]
