target extended localhost:3333
monitor halt
file build/ch.elf
monitor flash erase_sector 0 0 11
monitor flash write_image build/ch.elf
continue
quit
