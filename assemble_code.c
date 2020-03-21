#include "microcode/microcode.h"
#include <stdlib.h>
#include <stdio.h>

void write_code(void *code, uint64_t code_bytes, char *output_file) {
    FILE *output = fopen(output_file, "wb");
    fwrite(code, 1, code_bytes, output);
    fclose(output);
}

void assemble_code() {
    instruction_t instructions[2];
    instructions[0].data1 = 0;     // Register 0
    instructions[0].data2 = 0x123; // Move 0x123 to it
    instructions[0].instruction = instruction_mov; // Move instruction
    instructions[0].instruction_flags = INST_FLAG_SRC_CONST; // Src is constant

    instructions[1].data1 = 0;
    instructions[1].data2 = 0;
    instructions[1].instruction_flags = 0;
    instructions[1].instruction = instruction_hlt;

    write_code(&instructions, sizeof(instructions), "liquid_test.liq");
}

void main() {
    assemble_code();
}