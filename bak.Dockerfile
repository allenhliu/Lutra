FROM docker.oa.com:8080/library/tlinux2.2-with-agent:latest

WORKDIR /usr/src/test

ENV PATH=/opt/rh/rh-python36/root/usr/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH=/opt/rh/rh-python36/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
ENV MANPATH=/opt/rh/rh-python36/root/usr/share/man:$MANPATH
ENV PKG_CONFIG_PATH=/opt/rh/rh-python36/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}}
ENV XDG_DATA_DIRS="/opt/rh/rh-python36/root/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
ENV LANG zh_CN.utf8
ENV LC_ALL zh_CN.utf8
ENV PYTHONDONTWRITEBYTECODE 1
ENV NO_PROXY linux-mirror.tencent-cloud.com,tlinux-mirrorlist.tencent-cloud.com,localhost,.oa.com,.local,10.

RUN echo "各种源" \
    && rm /etc/yum.repos.d/tlinux.repo \
    && export http_proxy="http://web-proxy.tencent.com:8080" \
    && export https_proxy="http://web-proxy.tencent.com:8080" \
    && export no_proxy='10.,*.oa.com' \
    && wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.cloud.tencent.com/repo/centos7_base.repo \
    && sed -i 's/\$releasever/7/g' /etc/yum.repos.d/CentOS-Base.repo \
    && wget https://dl.google.com/linux/linux_signing_key.pub \
    && rpm --import linux_signing_key.pub \
    && echo -e '[google-chrome]' > /etc/yum.repos.d/google-chrome.repo \
    && echo 'name=google-chrome' >> /etc/yum.repos.d/google-chrome.repo \
    && echo 'baseurl=http://dl.google.com/linux/chrome/rpm/stable/$basearch' >> /etc/yum.repos.d/google-chrome.repo \
    && echo 'enabled=1' >> /etc/yum.repos.d/google-chrome.repo \
    && echo 'gpgcheck=1' >> /etc/yum.repos.d/google-chrome.repo \
    && echo 'gpgkey=https://dl-ssl.google.com/linux/linux_signing_key.pub' >> /etc/yum.repos.d/google-chrome.repo \
    && yum makecache fast \
    && yum -y update \
    && yum install --nogpgcheck -y bzip2 centos-release-scl java-1.8.0-openjdk google-chrome-stable wqy-microhei-fonts wqy-zenhei-fonts\
    && yum install --nogpgcheck -y rh-python36 \
    && echo "Allure" \
    && curl -o allure-2.8.0.zip -Ls https://github.com/allure-framework/allure2/releases/download/2.8.0/allure-2.8.0.zip \
    && unzip allure-2.8.0.zip -d /opt/ \
    && ln -s /opt/allure-2.8.0/bin/allure /usr/bin/allure && allure --version \
    && echo "ChromeDriver" \
    && wget https://chromedriver.storage.googleapis.com/2.44/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && echo "Firefox" \
    && wget -O FirefoxSetup.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US" \
    && tar xjf FirefoxSetup.tar.bz2 -C /opt/ \
    && ln -s /opt/firefox/firefox /usr/local/bin/ \
    && wget https://github.com/mozilla/geckodriver/releases/download/v0.23.0/geckodriver-v0.23.0-linux64.tar.gz \
    && tar -xvzf geckodriver* \
    && mv geckodriver /usr/bin/geckodriver \
    && chown root:root /usr/bin/geckodriver \
    && chmod +x /usr/bin/geckodriver

COPY *.py lutra.sh ../

COPY lutra ../lutra

RUN echo "Lutra" \
    && export http_proxy="http://web-proxy.tencent.com:8080" \
    && export https_proxy="http://web-proxy.tencent.com:8080" \
    && export no_proxy='10.,*.oa.com' \
    && pip install ../

ENTRYPOINT ["../lutra.sh"]

CMD ["-n", "4", "--reruns", "5"]