C_SOURCES = $(shell find src/ -type f -name '*.c')
OBJ = ${C_SOURCES:.c=.o}
CC = gcc

all: liquid_assemble liquid_cpu

liquid_cpu: ${OBJ}
	${CC} -o liquid_cpu ${OBJ}


liquid_assemble: assemble_code.c
	${CC} -O2 -I src assemble_code.c -o liquid_assemble

%.o: %.c
	${CC} -O2 -I src -c $< -o $@

clean:
	rm -rf ${OBJ}
	rm -rf liquid_cpu
	rm -rf liquid_assemble