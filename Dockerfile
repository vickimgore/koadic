FROM    ubuntu:19.10
WORKDIR /opt/koadic
RUN     apt update && apt install -y python3 python3-pip socat python-pip
COPY    . /opt/koadic
RUN     pip3 install -r requirements.txt && \
	pip2 install -r data/impacket/requirements.txt
ENTRYPOINT ["./koadic"]
