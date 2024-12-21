FROM ubuntu@sha256:fad5ba7223f8d87179dfa23211d31845d47e07a474ac31ad5258afb606523c0d as ubu

RUN apt update -y
RUN apt install make gcc -y
RUN mkdir /app
COPY src /app/src
COPY Makefile /app

WORKDIR /app
RUN make

RUN rm -rf src Makefile

FROM pwn.red/jail

COPY --from=ubu / /srv
COPY flag.txt /srv/app/flag.txt
COPY hook.sh /jail

RUN chmod +x /jail/hook.sh

ENV JAIL_MEM=100M JAIL_TMP_SIZE=1 JAIL_CPU=1000 JAIL_PORT=8181 JAIL_POW=0 JAIL_TIME=69
