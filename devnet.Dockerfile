FROM bk.artifactory.oa.com:8080/paas/public/tlinux2.2:latest

WORKDIR /data/landun/workspace

RUN echo "基础依赖" \
    && rpm --rebuilddb \
    && yum makecache fast \
    && yum -y update \
    && yum --enablerepo=tlinux-testing --nogpgcheck install -y openssl \
    && yum install --nogpgcheck -y bzip2 java-1.8.0-openjdk centos-release-scl wqy-microhei-fonts wqy-zenhei-fonts \
    && yum install --nogpgcheck -y rh-python36 \
    && echo "准备设置环境变量"

ENV PATH=/opt/rh/rh-python36/root/usr/bin${PATH:+:${PATH}} \
    LD_LIBRARY_PATH=/opt/rh/rh-python36/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}} \
    MANPATH=/opt/rh/rh-python36/root/usr/share/man:$MANPATH \
    PKG_CONFIG_PATH=/opt/rh/rh-python36/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}} \
    XDG_DATA_DIRS="/opt/rh/rh-python36/root/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=zh_CN.utf8 \
    LC_ALL=zh_CN.utf8

COPY binary ./

RUN echo "Chrome" \
    && rpm --rebuilddb \
    && yum --enablerepo=tlinux-testing --nogpgcheck install -y chromium chromedriver

RUN echo "Firefox" \
    && tar xjf firefox-*.tar.bz2 -C /opt/ \
    && ln -s /opt/firefox/firefox /usr/local/bin/ \
    && tar -xvzf geckodriver* \
    && mv geckodriver /usr/bin/geckodriver \
    && chown root:root /usr/bin/geckodriver \
    && chmod +x /usr/bin/geckodriver

RUN echo "Allure" \
    && unzip allure-*.zip -d /opt/ \
    && ln -s /opt/allure-2.12.1/bin/allure /usr/bin/allure && allure --version

COPY *.py lutra.sh ../

COPY lutra ../lutra

COPY swagger_ui_dist ../swagger_ui_dist

RUN echo "Lutra" \
    && pip install ../ -i http://mirrors.cloud.tencent.com/pypi/simple/ --trusted-host mirrors.cloud.tencent.com