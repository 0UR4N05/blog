# burg


## writeup
This challenge is quite cool, i've learned a lot of things while making it.  
[OSdev](https://wiki.osdev.org/Expanded_Main_Page) is a good resource that you might wanna check once you feel confused about something.
You also might wanna check [this](https://manybutfinite.com/post/how-computers-boot-up/) before reading this writeup because ill be skipping a lot of required knowledge due to simplicity.

### diving into challenge code
#### boot.s
Every good story begins in [real mode](https://wiki.osdev.org/Real_Mode), where we only have a few KB of segmented memory to work with.  
The program automatically hates its environement and decides to load an additional [3 sectors](https://www.ctyme.com/intr/rb-0607.htm) from the floppy disk before transitioning to protected mode.
```
	call	load_step1_5;			loading the second step from the second sector
	call	load_gdt;
```

Once in [protected mode](https://wiki.osdev.org/Protected_Mode), we no longer have access to BIOS interrupts.
After a successful switch to protected mode, the program jumps directly into C code.

#### burg.c
Finally, we’re looking at some C code!  
At first glance, it seems like it doesn’t do much but actually, it does the program asks for some input and display some.  

The program starts by printing messages and [asking for input](https://wiki.osdev.org/PS/2). We obviously can't directly exploit the output functions, the vulnerability lies in how it handles the input.

Here’s where the input function comes into play. It reads characters from the keyboard's serial port. But there’s a flaw in how it processes backspace, there's no check on how many times the backspace key is pressed.  
This means you can backspace past the beginning of the buffer, which lead to writing outside its bounds.

```c
uint32_t sgets(char *buffer, int mlen){
	int i = 0;
	uint8_t keystroke = 0;
	bool nt = false;
	while (keystroke != NL && i < mlen){
		keystroke = sread();
		if (keystroke == BACKSPACE){
			nt = true;
			i--;
		} else {
			buffer[i] = keystroke;
			if (nt == true){
				buffer[i + 1] = '\0';
				nt = false;
			}
			i++;
		}
	}
	swrite('\n');
	buffer[i] = '\0';
	return (uint32_t) i;
}
```

We know we can write beyond the buffer, but the question is where can we write? The answer: pretty much anywhere.

In my exploit, i decided to keep things simple and write to a comfort zone area: 0x7c00, where the first stage of the bootloader gets loaded.

### exploit
The exploit is nothing much, once we input username and password the c code is done and returns back to the bootloader area '0x7c75' where we injected our shellcode.  
But wait ? i hear you asking what's the point of a shellcode is we lack everything a shell a libc, we basically got nothing.  
Well the goal of this challenge is to read out of the disk and display the data in the screen, but without bios interrupts this can be done in two ways.  
Either returning back to real mode or writing a whole floppy disk driver, according to [this](https://wiki.osdev.org/Floppy_Disk_Controller) there is no fucking way im writing a floppy disk driver, so that leaves us one choise, returning to real mode.

#### pivoting back to real mode - breakking down the exploit
Well we're still in protected mode, so we we need so set a real mode GDT data segment before going back  
```
	mov ax, RDATA_SEG;
	mov ds, ax;
	mov es, ax;
	mov ss, ax;
	mov sp, 0xFFFF
```
Then a long jump into real mode code segement which lands us in rmode_stub  
```
	jmp 0x18:rmode_stub
```

Now that we're ready to go back we set cr0 and long jump in prot_to_real

```
	mov eax, cr0
	and eax, 0xfffffffe
	mov cr0, eax;
	jmp 0:prot_to_real
```

Alright now we ball, we're in real mode, so we set the registers and set the bios interrupts back
```
	xor	ax, ax
	mov	ds, ax
	mov	es, ax
	mov	ss, ax
	sti
```
with interrupts back we can call load_flag which loads the flag in 0x7d00 and print it.
