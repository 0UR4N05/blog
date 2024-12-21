SRC = src/main.cpp
NAME = run
CFLAGS = -mshstk -fno-stack-protector

$(NAME): $(SRC)
	g++ $(CFLAGS) $(SRC) -o $(NAME)

clean :
	rm -rf $(NAME)
