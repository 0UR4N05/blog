# not\_so\_average\_todo\_app
Call me average no more  

FLAG : ODESSEY{c4ll\_m3\_4v3r463\_n0\_m0r3\_5vp\_w4k4\_w4k4\_3h\_3h}  

## writeup
### checksec
```
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
The challenge is a todo app where we have choises either creating, listing, editing, dumping and loading todos.  

## Code analysis
### global variables
```c
FILE *x;                            
char *todos[TODOSZ] = {0};
uint32_t todosz[TODOSZ] = {0};
uint32_t todoit = 0;
```
