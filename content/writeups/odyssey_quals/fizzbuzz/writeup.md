# burg
1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, Fizz Buzz, 16, 17, Fizz, 19, Buzz, Fizz, 22, 23, Fizz, Buzz, 26, Fizz, 28, 29, Fizz Buzz, 31, 32, Fizz, 34, Buzz, Fizz, ...

## writeup 
This challenge has no exact solution; it depends on the instructions that fit the program's rules. In this article, I will only discuss my solution to it.  
The program asks us for the shellcode and then iterates over its bytes, making sure that the first byte is divisible by 3, the second is divisible by 5, and so on until it reaches the end of the shellcode.  

```c
	while (++i != SC_SIZE){
		if (buffer[i] == 0)
			continue;
		if (x == false){
			x = true;
			if (buffer[i] % 3 != 0){
				fabort();
			}
		} else {
			x = false;
			if (buffer[i] % 5 != 0){
				fabort();
			}
		}
	}
```

First, we need to know our enemies and our allies.  
We quite have a lot of allies in this challenge  
    1. we have a /bin/bash string in the stack  `slow_print("/bin/sh");`  (line 71)  
    2. the function slow_print before executing the shellcode `slow_print("executing...");` (line 68)  
    3. nop instruction and fs register.  
    4. a lot of space to execute a lot of repetitive instructions  

About the enemies, we have just one enemy: THE FILTER.  

First of all, the goal is to get a shell luckily syscall instruction does meet the filter's demmands.
### exploit

The exploit will be divided into 3 parts  
    1. Zero out the unused registers
    2. get '/bin/sh' in RSI
    3. get EXECVAT in rax
    4. syscall
    5. profit

#### zero out the unused registers
Step one is that we need to clear some registers [rax, rbx, rcx, rdx] a quick instruction that would do that is [cpuid](https://www.felixcloutier.com/x86/cpuid), first cpuid byte is divisible by 5 the use of a nop instruction before cpuid would help, also the last byte is divisible by 3 so we need something that resets us to 3 that is `fs`.

Another register that might cause us a problem is `RDI`, so we just `dec rdi; fs;`

Now with our registers zeroed out we could go to the next step.

#### Getting the "/bin/sh" in rsi
Here where that slow_print function comes into play, after it was executed it left a `.rodata` ptr in rdi,also there is another slow_print function that print "/bin/sh", so we know that "/bin/sh" and "executing..." strings are not that far appart in the rodata section.  
That means all we need to do is to increment or decrement rsi to find the perfect offset and land on "/bin/sh".  
`inc rsi;` got 3 bytes that satisfy the filter, and we add an `fs` to reset again the divisibility to 3.  

#### get EXECVAT in rax
Well it seems that `inc rax;` also fits the filter, but execveat syscall number is 322 so we just keep incrementing until we achieve it, im quite sure that someone solved it in a better way but yeah that works too.  

#### syscall and profit
Well rsi is set to the /bin/sh rax is 322 and we got to do is to call a syscall and profit.  


I know this might seem a bit confusing, if you feel confused just read the article again or reach out to me.
