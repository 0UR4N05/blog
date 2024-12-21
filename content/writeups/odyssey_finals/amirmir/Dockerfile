FROM ubuntu as ubu

FROM pwn.red/jail

COPY --from=ubu / /srv

COPY run /srv/app/run
COPY flag.txt /srv/app/flag.txt

ENV JAIL_MEM=300M JAIL_TMP_SIZE=1 JAIL_CPU=3500 JAIL_PORT=9191 JAIL_POW=0 JAIL_TIME=6900
