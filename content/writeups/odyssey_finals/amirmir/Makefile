SRC = src/main.c
NAME = run
CFLAGS = -no-pie -lseccomp

$(NAME): $(SRC)
	gcc $(CFLAGS) $(SRC) -o $(NAME)

clean :
	rm -rf $(NAME)
