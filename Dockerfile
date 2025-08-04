FROM ubuntu:latest

RUN apt-get update && apt-get install -y sudo bash

RUN useradd -m -s /bin/bash user && \
    passwd -d user && \
    echo "user ALL=(ALL) NOPASSWD: ALL" | EDITOR='tee -a' visudo && \
    sed -i '/user ALL=(ALL) NOPASSWD: ALL/d' /etc/sudoers

RUN chsh -s /bin/bash user

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

USER root

CMD ["/bin/bash"]

