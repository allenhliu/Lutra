#FROM bk.artifactory.oa.com:8090/paas/public/tlinux2.2:latest
FROM csighub.tencentyun.com/admin/tlinux2.2-bridge-base-tcloud:1.0.0

WORKDIR /data/workspace

RUN echo "基础依赖" \
    && rpm --rebuilddb \
    && yum makecache fast \
    && yum -y update \
    && yum install --nogpgcheck -y bzip2 java-1.8.0-openjdk centos-release-scl wqy-microhei-fonts wqy-zenhei-fonts git libXScrnSaver* at-spi2-atk gtk3\
    && yum install --nogpgcheck -y rh-python36 rh-nodejs10 \
    && echo "准备设置环境变量"

RUN mkdir -p $HOME/.ssh/ \
    && touch $HOME/.ssh/config \
    && echo -e "Host *-svn.tencent.com\n  StrictHostKeyChecking no\nPort 22\nHost git.code.oa.com\n  StrictHostKeyChecking no\nHostName git.code.oa.com\nPort 22\n" > $HOME/.ssh/config

ENV PATH=/opt/rh/rh-nodejs10/root/usr/bin${PATH:+:${PATH}} \
    LD_LIBRARY_PATH=/opt/rh/rh-nodejs10/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}} \
    PYTHONPATH=/opt/rh/rh-nodejs10/root/usr/lib/python2.7/site-packages${PYTHONPATH:+:${PYTHONPATH}} \
    MANPATH=/opt/rh/rh-nodejs10/root/usr/share/man:$MANPATH \
    PUPPETEER_DOWNLOAD_HOST=http://tnpm.oa.com/mirrors \
    PUPPETEER_CHROMIUM_REVISION=674921

COPY binary ./

RUN echo "借助puppeteer安装chromium" \
    && npm config set registry http://r.tnpm.oa.com \
    && npm install -g --unsafe-perm=true --allow-root puppeteer \
    && cp -r /opt/rh/rh-nodejs10/root/usr/lib/node_modules/puppeteer/.local-chromium/linux-*/chrome-linux /usr/local/ \
    && ln -snf /usr/local/chrome-linux/chrome /usr/bin/chrome \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && echo "已安装版本号`chrome --version`"

RUN echo "Firefox" \
    && tar xjf firefox-*.tar.bz2 -C /opt/ \
    && ln -s /opt/firefox/firefox /usr/local/bin/ \
    && tar -xvzf geckodriver* \
    && mv geckodriver /usr/bin/geckodriver \
    && chown root:root /usr/bin/geckodriver \
    && chmod +x /usr/bin/geckodriver

RUN echo "Allure" \
    && unzip allure-*.zip -d /opt/ \
    && ln -s /opt/allure-2.13.6/bin/allure /usr/bin/allure && allure --version

ENV PATH=/opt/rh/rh-python36/root/usr/bin${PATH:+:${PATH}} \
    LD_LIBRARY_PATH=/opt/rh/rh-python36/root/usr/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}} \
    MANPATH=/opt/rh/rh-python36/root/usr/share/man:$MANPATH \
    PKG_CONFIG_PATH=/opt/rh/rh-python36/root/usr/lib64/pkgconfig${PKG_CONFIG_PATH:+:${PKG_CONFIG_PATH}} \
    XDG_DATA_DIRS="/opt/rh/rh-python36/root/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=zh_CN.utf8 \
    LC_ALL=zh_CN.utf8

COPY *.py lutra.sh ../

COPY lutra ../lutra

COPY swagger_ui_dist ../swagger_ui_dist

RUN pip install --upgrade pip

RUN echo "Landun SDK" \
    && pip install python_atom_sdk  -i http://mirrors.devops.oa.com/pypi/simple/ --extra-index-url http://mirrors.devops.oa.com/pypi/simple/ --trusted-host mirrors.devops.oa.com

RUN echo "setup_requires for pytest-forked" \
    && pip install setuptools_scm  -i http://mirrors.devops.oa.com/pypi/simple/ --extra-index-url http://mirrors.devops.oa.com/pypi/simple/ --trusted-host mirrors.devops.oa.com

RUN echo "Lutra" \
    && pip install ../ -i http://mirrors.tencent.com/pypi/simple/ --trusted-host mirrors.tencent.com