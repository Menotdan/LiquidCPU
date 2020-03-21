#include "cpu.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void execute_binary_liquid_cpu(char *filename) {
    cpu_t my_cpu;
    setup_cpu(&my_cpu);

    printf("[Liquid Main] Set up CPU state..\n");

    /* Load the binary into memory */
    FILE *size_get = fopen(filename, "r");
    fseek(size_get, 0, SEEK_END);
    int64_t fsize = ftell(size_get);
    fclose(size_get);

    printf("[Liquid Main] Got executable size %ld.\n", fsize);

    FILE *liquid_exec = fopen(filename, "rb");

    uint8_t *exec = malloc(fsize);
    fread(exec, 1, fsize, liquid_exec);
    fclose(liquid_exec);

    printf("[Liquid Main] Loaded binary.\n");

    /* Copy to CPU memory area */
    memcpy(my_cpu.memory, exec, fsize);
    free(exec);

    printf("[Liquid Main] Binary is in CPU memory.\n");

    /* Run CPU */
    cpu_code_loop(&my_cpu);
}

void main() {
    execute_binary_liquid_cpu("liquid_test.liq");
}