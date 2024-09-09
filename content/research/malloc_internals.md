Before you start reading this blog, keep in mind this isnt a tutorial, these are personal notes about analysing heap source code, you most likey not going to understand anything here its just messy, you better off reading other blogs about heap than this, thanks.  

# prerequisites
## tcache
tcache (thread local caching) introduced on glibc 2.26 the purpose of adding this is improving preformance  
each thread is allocated with its own tcache struct, it behaves like a normal arena but isnt shared between threads  
all tcache chunks are saved as tcache_entry as a linked list  
```c  
typedef struct tcache_entry
{
  struct tcache_entry *next;
  /* This field exists to detect double frees.  */
  uintptr_t key;
} tcache_entry;
```
a single tcache entry looks like this  
```c
typedef struct tcache_perthread_struct
{
  char counts[TCACHE_MAX_BINS];
  tcache_entry *entries[TCACHE_MAX_BINS];
} tcache_perthread_struct;
```
this struct hold up to 64 sizes of bins but hold 7 bins on single cell  
tcache only holds sizes from 0x20 to 0x410  
tcaches are similar to fast bins, singly linked lists with a specific size  
Note that tcache entries use pointers to user data rather than chunk metadata.  

## fast bins  
there are 10 fast bins holding sizes from 32 to MAX_FAST_SIZE `(80 * sizeof(size_t) / 4)` "including metadata"  
all these bins are single linked lists so addition and deletion is LIFO  

## small bins  
62 small bins, small bins are faster than large bins but slower than fastbins  
They are doubly linked lists, Insertions happen at the head while removal happens at the tail {FIFO}  

## large bins  
63 large bins, the slowest of bins   
doubly linked list  
store ranges of sizes sorted in decreasing order (largest chunk at head to the smallest at tails)  

## mstate->state
1 unsorted bins -> 62 small bins -> 63 large bins  

# structs

# macros
MAYBE_INIT_TCACHE()         [malloc.c:3276]  
checks if tcache is null  
if not  
    calls `tcache_init()`  

PROTECT_PTR(pos, ptr)       [malloc.c:339]  
    return (pos >> 12) ^ ptr  

REVEAL_PTR(tcache_entry *ep)        [malloc.c:331]  
    PROTECT_PTR(&ep, ep);  

# functions

## void unlink_chunk(mstate av, mchunkptr p)            [malloc.c:1608]
starts by verifying the integrity of the chunk by checking the size of the current chunk and next_chunk->prev_size  
checks next chunk bk == p and back chunk fd == p  
unlink the chunk by removing its ptrs   
    fd->bk = p->bk  
    bk->fd = p->fd  
if chunk is from large bin  
    same shenanigans happens here quick checks on the integrity of the large bin  

## void malloc_consolidate(mstate av)                    [malloc.c:4810]  
description:  
  malloc_consolidate is a specialized version of free() that tears  
  down chunks held in fastbins.  Free itself cannot be used for this  
  purpose since, among other things, it might place chunks back onto  
  fastbins.  So, instead, we need to use a minor variant of the same  
  code.  
gets a ptr of unsorted bins  
iterates over fast bins  
    iterates over the selected fast bin  
        - checks if the current **chunk is aligned**  
        - checks if the current **chunk's size equals the bin's size**  
        - checks if the current chunk is **not in use**  
        - reveals the chunk's fd calling it **next_p**  
        now we must consolidate p with next_p  
        - size = chunk size   
        - next_chunk = p + size  
        - nextsize = next_chunk size  
        the function checks if the previous chunk is not in use using PREV_INUSE flag  
        - prevsize = p->prev_size  
        - p = p - prev_size  
        this is literally accessing the chunk before the current chunk  
        - check p chunk's size with next_size  
        - call `unlink_chunk(av, p)`  
        - then puts the result in unsorted bin  


## void alloc_perturb(char *p, size_t n)                [malloc.c:1983]  
check if pertrub_byte is enabled  
memsets p with pertub_byte ^ 0xff  

## void *_int_malloc (mstate av, size_t bytes)          [malloc.c:3845]  
this is what i would call the meat of malloc  
starts by checking the alignement of the requested bytes  
if the arena ptr is NULL  
    it requests more memory using sysmalloc  
**fast_bin**  
if the size falls in the fastbin range  
    - gets the index of fast bin range using fastbin_index macro  
    - using that idx `int_malloc` calls `fast_bin(av, idx)` to get a pointer getting  
    the right size bin  
    if there is a chunk in the bin that could be served **we will call that chunk victim**  
        - checks if the victim addr is aligned  
        - reveal the victim's fd ptr and sets it as the first chunk in fastbin  
        - checks the size of the victim if it matches the bin it belongs in  
        - do some quick checks using `do_check_remalloced_chunk()`  
        **tcache integration**  
        while we're here lets see if there's other chunks of the same size and store them in tcache  
        func gets tcache_idx based on the size of the fastbin  
        if tcache != NULL and the tc_idx is smaller than tcache_bins max size  
            while tcache isn't full and fastbin isn't empty  
                - check the alignement of the chunk in fst bin  
                - remove it from fast_bin  
                - insert it to tcache using `tcache_put`  
        - convert the victim from chunk to mem  
        - call `alloc_perturb(char *p, size_t n)`  
        - return the usable memory to the user  
well not lucky? your chunk not found in fastbin  
**small bin**  
if the size falls on smallbin range  
    - get index  
    - get the first bin using the index  
    - victim = last chunk in the bin  
    if the victim doesnt the address of the bin "malloc_init sets every bin using its address"  
        if victim->bk->fd != victim  
            well you fucked up  
        - set inuse bit  
        - first_chunk in small_bin = vict  
**consolidation**  
neither fast/small/tcache can't serve back the request what if we have the ability to serve it but  
the chunks are so divided, we must consolidate'em all  
idx is filled with the convinient large bin index  
if (av have fast_bins)  
    call `malloc_consolidate(av)`  
  
**unsorted bins**  
infinite loop  
    iterates over unsorted chunks  
        quick checks to make sure thath the chunk is alright  
            - check if the chunk's size of bigger than system_mem "the limit of a non mmaped chunk"  
            - also checks the next chunk if its bigger than system_mem  
            - check the next chunk's fd if it matches the current chunk  
            - check if the prev in use of next is set to true  
        if the size of the requested chunk falls in smallbin range   
            and the selected chunk unsorted chunk is the last remainder chunk  
            and unsorted chunk's size > requested size  
                split the chunk and reattach the remainder  
**large bin**  
TODO  
  

## void *tcache_get_n (size_t tc_idx, tcache_entry **ep) [malloc.c:3174]  
checks if the given ep equals the address of `&(tcache->entries[tc_idx])`  
if no it `REVEAL_PTR(*ep)`  
then checks if the chunk is aligned   
if ep == &(tcache->entries[tc_idx])  
    `REVEAL_PTR(*ep->next)`  
else   
    `PROTECT_PTR(*ep->next)`  
decrements the cache count and sets the key for the tcache to 0  
then returns the free chunk  

## void *tcache_get (size_t tc_idx)        [malloc.c:3197]  
tcache_get takes the indexes the chunk and calls `tcache_get_n`  
  
## void tcache_init(void);                      [malloc.c:3242]  
locks the arena using `arena_get`  
allocates a `tcache_perthread_struct` using `_int_malloc`  
unlocks the arena  
sets tcache global variable to the recently allocated `tcache_perthread_struct`  
and memsets it with zeros  
  
##  static void malloc_init_state (mstate av)   [malloc.c:1940]  
the function starts by filling the bins with the address of the bins  
if (not main_arena)  
    sets its flag as noncontiguous  
if (main_arena)  
    then set the max_fast_bin size  
sets have fastchunks to false  

## uint32_t random_bits(void)                   [include/random-bits.h]  
__clock_gettime64 (CLOCK_MONOTONIC, &tv);  
ret = nanosec ^ sec;  
ret ^=  ret << 24 | ret >> 8;  

## void tcache_key_initialize (void)            [malloc.c:3140]  
gets random bytes using `random_bits`  
if libc 32bit  
    sets tcache_key to rim->bk  
        - victim->bk = fd  
        basically just removing the node from the circular list  
        if av != &main_arena  
            set non main_arena bit  
        remember **tcache integration**  
        repeat same code here  
        - convert the victim to usable memory  
        - call `alloc_perturb()`  
        - return the usable memory  
  
## void *tcache_get_n (size_t tc_idx, tcache_entry **ep) [malloc.c:3174]  
checks if the given ep equals the address of `&(tcache->entries[tc_idx])`  
if no it `REVEAL_PTR(*ep)`  
then checks if the chunk is aligned   
if ep == &(tcache->entries[tc_idx])  
    `REVEAL_PTR(*ep->next)`  
else     
    `PROTECT_PTR(*ep->next)`    
decrements the cache count and sets the key for the tcache to 0  
then returns the free chunk  
  
## void *tcache_get (size_t tc_idx)        [malloc.c:3197]  
tcache_get takes the indexes the chunk and calls `tcache_get_n`  
  
## void tcache_init(void);                      [malloc.c:3242]  
locks the arena using `arena_get`  
allocates a `tcache_perthread_struct` using `_int_malloc`  
unlocks the arena  
sets tcache global variable to the recently allocated `tcache_perthread_struct`  
and memsets it with zeros  
  
##  static void malloc_init_state (mstate av)   [malloc.c:1940]  
the function starts by filling the bins with the address of the bins  
if (not main_arena)  
    sets its flag as noncontiguous  
if (main_arena)  
    then set the max_fast_bin size  
sets have fastchunks to false  
  
## uint32_t random_bits(void)                   [include/random-bits.h]  
__clock_gettime64 (CLOCK_MONOTONIC, &tv);  
ret = nanosec ^ sec;  
ret ^=  ret << 24 | ret >> 8;  
  
## void tcache_key_initialize (void)            [malloc.c:3140]  
gets random bytes using `random_bits`  
if libc 32bit  
    sets tcache_key to random_bits  
else   
    sets tcache to (tcache_key << 32) | random_bits  
  
## void ptmalloc_init (void)                    [arena.c:262]  
sets `__malloc_initialized` to true  
if (tcache is used)  
    calls `tcache_key_initialize()`  
proceeds to set some mtag tunables   
sets the `thread_arena` to `main_arena`  
calls malloc_init_state(&main_arena)  
now the main_arena is initialized the function continues to get other tunables [mmap_max, arena_max, tcache_max...]  
if mp_.hqpagesize > 0  
    set mmapthreshold to hq_pagesize  
this condition is set to force mmap for main arena instead of sbrk  
  
##  void *__libc_malloc (size_t bytes)          [malloc.c:3293]  
checks if malloc is initialized using `__malloc_initialized` global var  
if (NO):  
    calls `ptmalloc_init()`;  
if tcache   
    checks if the request is gonna overflow when aligned and returns an   
    index for tcache  
    if (yes)  
        set errno to ENOMEM  
        return (NULL)  
    calculates the index of chunk in tcache  
    calls `MAYBE_INIT_TCACHE()` to init the tcache  
    In case tcache was never initialized now its locked and loaded  
    if the request could fit in a tcache list and that list contains free nodes  
        call `tcache_get()`  
        return the free chunk  
    malloc locks the heap  
    calls `_int_malloc(malloc_state, bytes)`  
