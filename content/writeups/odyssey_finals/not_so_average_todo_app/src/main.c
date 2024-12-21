#include <stdio.h>
#include <linux/limits.h>
#include <fcntl.h>
#include <math.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <sys/syscall.h>

#define TODOSZ 1024

FILE *x;
char *todos[TODOSZ] = {0};
uint32_t todosz[TODOSZ] = {0};
uint32_t todoit = 0;

void menu();

void restore_handler(){
    uint32_t	i = 0;
    puts("SEGFAULT... EXITING.");
    while (i < todoit){
	free(todos[i]);
    }
    fclose(x);
    sleep(5);
    syscall(SYS_exit, EXIT_SUCCESS);
}

//https://github.com/akhileshthite/3d-donut/blob/main/Donut.c
void spinning_donut(){
    float A = 0, B = 0;
    float i, j;
    int k;
    float z[1760];
    char b[1760];
    printf("\x1b[2J");
    for(;;) {
        memset(b,32,1760);
        memset(z,0,7040);
        for(j=0; j < 6.28; j += 0.07) {
            for(i=0; i < 6.28; i += 0.02) {
                float c = sin(i);
                float d = cos(j);
                float e = sin(A);
                float f = sin(j);
                float g = cos(A);
                float h = d + 2;
                float D = 1 / (c * h * e + f * g + 5);
                float l = cos(i);
                float m = cos(B);
                float n = sin(B);
                float t = c * h * g - f * e;
                int x = 40 + 30 * D * (l * h * m - t * n);
                int y= 12 + 15 * D * (l * h * n + t * m);
                int o = x + 80 * y;
                int N = 8 * ((f * e - c * d * g) * m - c * d * e - f * g - l * d * n);
                if(22 > y && y > 0 && x > 0 && 80 > x && D > z[o]) {
                    z[o] = D;
                    b[o] = ".,-~:;=!*#$@"[N > 0 ? N : 0];
                }
            }
        }
        printf("\x1b[H");
        for(k = 0; k < 1761; k++) {
            putchar(k % 80 ? b[k] : 10);
            A += 0.00004;
            B += 0.00002;
        }
        usleep(30000);
	char buff;
	if (read(0, &buff, 1) == 1){
	    return;
	}
    }
}

void alarm_handler(){
    // creating a new session
    printf("\e[1;1H\e[2J");
    fcntl(0, F_SETFL, fcntl(0, F_GETFL) | O_NONBLOCK);
    spinning_donut();
    fcntl(0, F_SETFL, 2);
    printf("\e[1;1H\e[2J");
    puts("new session loaded");
    menu();
}

void  __attribute__((constructor)) ignore_me(){
        setvbuf(stdin, 0, _IONBF, 0);
        setvbuf(stdout, 0, _IONBF, 0);
        setvbuf(stderr, 0, _IONBF, 0);
	char file[] = "/tmp/todo_XXXXXX";
	uint8_t fd = mkstemp(file);
	x = fdopen(fd, "r");
	bzero(todos, sizeof(char *) * TODOSZ);
}

void create_todo(){
    if (todoit + 1 > TODOSZ) {
	puts("Thats enough accomplishments for today, you can go sleep now.");
	syscall(SYS_exit, EXIT_SUCCESS);
    }
    printf("Todo size >> ");
    scanf("%d", &todosz[todoit]);
    getchar();
    if (todosz[todoit] > 500){
	puts("less detail please, im only a cli tool");
	return;
    }
    todos[todoit] = (char *) malloc(todosz[todoit] + 1);
    if (todos[todoit] == NULL)
	return ;
    printf("TODO >> ");
    read(0, todos[todoit], todosz[todoit]);
    puts("todo created, go grind now");
    todoit++;
}

void list_todos(){
    uint32_t it = 0;
    while (it < todoit){
	printf("[ ] - %s\n", todos[it]);
	it++;
    }
};

void dump_todos(){
    puts("saving and exiting");
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

void load_todos(){
    int size;
    printf("filename size >> ");
    scanf("%d", &size);
    getchar();
    if (size > (PATH_MAX / 4)){
	printf("nop not opening this");
	return ;
    }
    char *buffer = malloc(size);
    printf("filename >> ");
    read(0, buffer, 77);
    if (strlen(buffer) > 20){
	printf("still too long");
    }
    printf("TODOs are loading");
}

void edit_todo(){
    printf("todo index >> ");
    uint32_t idx = 0;
    scanf("%d", &idx);
    getchar();
    if (idx > todoit){
	puts("todo doesn't exist");
	return;
    }
    printf("todo >> ");
    read(0, todos[idx], todosz[idx]);
    puts("Todo modified");
}


void menu(){
    while (1){
	printf(
		"1. create a todo\n"
		"2. list todos\n"
		"3. edit a todo\n"
		"4. dump todos\n"
		"5. load todos\n"
		"6. exit\n"
		">> "
		);
	int uchoise;
	scanf("%d", &uchoise);
	getchar();
	switch (uchoise){
	    case 1:
		create_todo();
		break;
	    case 2:
		list_todos();
		break;
	    case 3:
		edit_todo();
		break;
	    case 4:
		dump_todos();
		break;
	    case 5:
		load_todos();
		break;
	    case 6 :
		exit(EXIT_SUCCESS);
	}
    }
}


int main(){
    signal(SIGSEGV, restore_handler);
    signal(SIGALRM, alarm_handler);
    alarm(20);
    menu();
}
