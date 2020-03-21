#include "opcode_handlers.h"
#include <stdio.h>

void unhandled_fault(cpu_t *cpu) {
    printf("[LiquidCPU] Unhandled fault at IP = 0x%lx and SP = 0x%lx\n", cpu->ip, cpu->sp);
}

void fault(cpu_t *cpu, uint64_t fault_no) {
    if (!cpu->reg_int_vector) {
        unhandled_fault(cpu);
    }

    (void) fault_no; // Unused for now
}

uint64_t *get_gpr(cpu_t *cpu, uint64_t register_info) {
    uint64_t *ret = (uint64_t *) 0;
    switch (register_info) {
        case reg_r0:
            ret = &cpu->r0;
            break;
        case reg_r1:
            ret = &cpu->r1;
            break;
        case reg_r2:
            ret = &cpu->r2;
            break;
        case reg_r3:
            ret = &cpu->r3;
            break;
        case reg_r4:
            ret = &cpu->r4;
            break;
        case reg_r5:
            ret = &cpu->r5;
            break;
        case reg_r6:
            ret = &cpu->r6;
            break;
        case reg_r7:
            ret = &cpu->r7;
            break;
        default:
            break;
    }

    return ret;
}

void move_handler(cpu_t *cpu, instruction_t *instruction) {
    uint64_t *src;
    uint64_t *dst;
    uint64_t src_const;
    uint64_t dst_const;

    /* Handle different src cases */
    if (instruction->instruction_flags & INST_FLAG_SRC_MEM_OP) {
        // we dont handle memory moves yet
        printf("[LiquidCPU] Warning, unhandled memory OP.\n");
    } else if (instruction->instruction_flags & INST_FLAG_SRC_CONST) {
        // Set src const, for garbage consistent interface for movement
        src_const = instruction->data2;
        src = &src_const;
    } else {
        // register move
        src = get_gpr(cpu, instruction->data2);
        if (!src) fault(cpu, fault_bad_reg);
    }

    /* Handle different dst cases */
    if (instruction->instruction_flags & INST_FLAG_DST_MEM_OP) {
        // we dont handle memory moves yet
        printf("[LiquidCPU] Warning, unhandled memory OP.\n");
    } else if (instruction->instruction_flags & INST_FLAG_DST_CONST) {
        // dst constants must be memory operands as well :thinkong:
        printf("[LiquidCPU] Warning, unhandled memory OP. (Through register)\n");
    } else {
        dst = get_gpr(cpu, instruction->data1);
        if (!dst) fault(cpu, fault_bad_reg);
    }

    *dst = *src;
}

void jmp_handler(cpu_t *cpu, instruction_t *instruction) {
    if (instruction->instruction_flags & INST_FLAG_DST_MEM_OP) {
        printf("[LiquidCPU] Warning, unhandled memory OP.\n");
    } else if (instruction->instruction_flags & INST_FLAG_DST_CONST) {
        cpu->ip = instruction->data1;
    } else {
        // register op
        uint64_t *jmp_loc = get_gpr(cpu, instruction->data1); // Get the GPR from this reg no
        if (!jmp_loc) {
            fault(cpu, fault_bad_reg);
        } else {
            cpu->ip = *jmp_loc; // Get the register's data
        }
    }
}

void hlt_handler(cpu_t *cpu, instruction_t *instruction) {
    cpu->flag |= CPU_FLAG_HLT;
}