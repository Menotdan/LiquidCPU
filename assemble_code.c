#include "microcode/microcode.h"
#include <stdlib.h>
#include <stdio.h>

uint64_t get_addr_inst(uint64_t instruction) {
    return instruction * sizeof(instruction_t);
}

void write_code(void *code, uint64_t code_bytes, char *output_file) {
    FILE *output = fopen(output_file, "wb");
    fwrite(code, 1, code_bytes, output);
    fclose(output);
}

void assemble_code() {
    instruction_t instructions[4];
    instructions[0].data1 = reg_r0;     // Register 0
    instructions[0].data2 = get_addr_inst(1); // Move the addr of the next instruction
    instructions[0].instruction = instruction_mov; // Move instruction
    instructions[0].instruction_flags = INST_FLAG_SRC_CONST | INST_FLAG_DST_REG; // Src is constant, and dst is a reg
    instructions[0].operand_size_src = operand_8;
    instructions[0].operand_size_dst = operand_8;

    instructions[1].data1 = reg_r1;
    instructions[1].data2 = 0;
    instructions[1].instruction = instruction_inc;
    instructions[1].instruction_flags = INST_FLAG_DST_REG;
    instructions[1].operand_size_dst = operand_8;

    /* Data */
    instructions[2].data1 = reg_r0;
    instructions[2].data2 = 0;

    /* Instruction and flags */
    instructions[2].instruction = instruction_jmp;
    instructions[2].instruction_flags = INST_FLAG_DST_REG;

    /* Operand sizes */
    instructions[2].operand_size_dst = operand_8;

    instructions[3].data1 = 0;
    instructions[3].data2 = 0;
    instructions[3].instruction = instruction_hlt;
    instructions[3].instruction_flags = 0;

    write_code(&instructions, sizeof(instructions), "liquid_test.liq");
}

void main() {
    assemble_code();
}