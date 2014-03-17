target extended localhost:3333
monitor reset init
monitor halt
monitor poll
monitor flash probe 0
file build/ch.elf
load build/ch.elf
continue
