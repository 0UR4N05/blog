#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <strings.h>
#include <fcntl.h>
#include <seccomp.h>
#include <sys/mman.h>

#define EXECSPZ 28

char flag[1024];

void read_flag(){
    int fd = open("./flag.txt", O_RDONLY);
    if (fd < 0){
	puts("Please contact lmongol asap.");
	exit(EXIT_FAILURE);
    }
    flag[read(fd, flag, 1000)] = '\0';
}

void  __attribute__((constructor)) ignore_me(){
        setvbuf(stdin, 0, _IONBF, 0);
        setvbuf(stdout, 0, _IONBF, 0);
        setvbuf(stderr, 0, _IONBF, 0);
        alarm(128);
}

void set_env(){
    scmp_filter_ctx ctx;
    ctx = seccomp_init(SCMP_ACT_KILL);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(nanosleep), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit), 0);
    seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(sigreturn), 0);
    if (seccomp_load(ctx) < 0){
	puts("Something went wrong, contact lmngol hh");
	exit(EXIT_FAILURE);
    }
}

void *create_execsp(){
    void *execsp = mmap((void *) 0x0, EXECSPZ, PROT_READ | PROT_WRITE | PROT_EXEC, 
		    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    bzero(execsp, EXECSPZ);
    return (execsp);
}

int main(){
    puts("bYHB1HcARn8");
    read_flag();
    // setupping the page
    void *execsp = create_execsp();
    printf("shellcode please >> ");
    read(0, execsp, EXECSPZ);
    set_env();
    ((void (*) (void)) execsp) ();
    // badtrip 
}
