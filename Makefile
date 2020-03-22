C_SOURCES = $(shell find src/ -type f -name '*.c')
OBJ = ${C_SOURCES:.c=.o}
CC = gcc

all: liquid_cpu

liquid_cpu: ${OBJ}
	${CC} -o liquid_cpu ${OBJ}

%.o: %.c
	${CC} -g -O2 -I src -c $< -o $@

clean:
	rm -rf ${OBJ}
	rm -rf liquid_cpu