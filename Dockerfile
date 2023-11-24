FROM ubuntu:23.04 AS install_pip_environment
COPY requirements.txt requirements.txt
RUN        set -x \
        && apt update \
        && DEBIAN_FRONTEND=noninteractive apt install -y python3-pip \
        && pip install --break-system-packages --no-cache-dir -U pip \
        && pip install --break-system-packages --no-cache-dir -U wheel \
        && pip install --break-system-packages --no-cache-dir -r requirements.txt \
        && apt-get clean -y \
        && rm -rf /var/lib/apt/lists/*

FROM install_pip_environment AS implementation
# This split allows the first part, requiring installations, to be skipped unless the installed packages change
COPY excel_converter.py /opt/excel_converter/excel_converter.py
ENV PATH=${PATH}:/opt/excel_converter
WORKDIR /opt/excel_converter/
CMD ["/usr/bin/sleep", "infinity"]
