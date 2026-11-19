FROM python:3.15.2-slim-trixie
RUN apt-get update \
    && apt-get install --yes --no-install-recommends flatpak python3-gi python3-gi-cairo librsvg2-common gir1.2-gtk-3.0 xvfb xauth xdotool desktop-file-utils \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 quasar
WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1
COPY xquasar/ xquasar/
COPY tests/ tests/
COPY packaging/ packaging/
RUN sh packaging/build-deb.sh 0~dev /tmp/xquasar.deb \
    && dpkg -i /tmp/xquasar.deb \
    && desktop-file-validate /usr/share/applications/xquasar.desktop \
    && (cd / && /usr/bin/xquasar --help) \
    && rm /tmp/xquasar.deb
USER quasar
CMD ["sh", "-ec", "python -m unittest discover -s tests -v && xvfb-run -a /usr/bin/python3 packaging/test-desktop.py"]
