FROM archlinux@sha256:5906892165fc79b4e282e36f24802528bcee2bd2896982ad771045341e15db5c as arch

RUN pacman -Syy --noconfirm
RUN pacman -S --noconfirm make gcc
RUN mkdir /app
COPY src /app/src
COPY Makefile /app

WORKDIR /app
RUN make

RUN rm -rf src Makefile

FROM pwn.red/jail

COPY --from=arch / /srv
COPY flag.txt /srv/app/flag.txt

ENV JAIL_MEM=100M JAIL_TMP_SIZE=1 JAIL_CPU=1000 JAIL_PORT=7171 JAIL_POW=0 JAIL_TIME=69
