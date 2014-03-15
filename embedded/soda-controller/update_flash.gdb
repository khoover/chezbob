target extended localhost:3333
monitor halt
file build/ch.elf
monitor flash write_image erase build/ch.bin
continue
exit
