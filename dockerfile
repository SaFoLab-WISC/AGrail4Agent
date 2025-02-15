FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sudo \
    && apt-get clean


RUN echo "root:rootpassword" | chpasswd && \
    usermod -aG sudo root


RUN id -u user || useradd -ms /bin/bash user && \
    echo "user:userpassword" | chpasswd


RUN mkdir -p /home/root /home/user && \
    chown -R root:root /home/root && \
    chown -R user:user /home/user


RUN passwd -d root


RUN chmod 700 /home/root


USER user


CMD ["/bin/bash"]
