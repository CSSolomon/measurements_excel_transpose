FROM ubuntu:latest AS install_pip_environment
COPY requirements.txt requirements.txt
RUN        apt update \
        && DEBIAN_FRONTEND=noninteractive apt install -y python3-pip \
        && pip install --no-cache-dir \
            -U pip==23.0.1 \
        && pip install --no-cache-dir \
            -r requirements.txt\
        && apt-get clean -y \
        && rm -rf /var/lib/apt/lists/*

FROM install_pip_environment AS implementation
# This split allows the first part, requiring installations, to be skipped unless the installed packages change
COPY excel_converter.py /opt/excel_converter.py
