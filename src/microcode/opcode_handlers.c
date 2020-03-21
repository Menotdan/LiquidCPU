#include "opcode_handlers.h"
#include <stdio.h>

void unhandled_fault(cpu_t *cpu) {
    printf("[LiquidCPU] Unhandled fault at IP = 0x%lx and SP = 0x%lx\n", cpu->ip, cpu->sp);
    while (1) {}
}

/* Fault */
void fault(cpu_t *cpu, uint64_t fault_no) {
    printf("[LiquidCPU] Got fault: %lu\n", fault_no);
    if (!cpu->reg_int_vector) {
        unhandled_fault(cpu);
    }

    (void) fault_no; // Unused for now
}

/* Get GPR from register no */
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

/* mov opcode */
void move_handler(cpu_t *cpu, instruction_t *instruction) {
    uint64_t *src;
    uint64_t *dst;
    uint64_t src_const;
    uint64_t dst_const;

    /* Handle different src cases */
    if (instruction->instruction_flags & INST_FLAG_SRC_MEM_OP) {
        /* If the memory op is from a register */
        if (instruction->instruction_flags & INST_FLAG_SRC_REG) {
            /* It is a memory operation through a register */
            uint64_t *reg = get_gpr(cpu, instruction->data2);
            if (!reg) {
                fault(cpu, fault_bad_reg);
            }

            uint64_t addr = *reg;
            if (!is_valid_addr(cpu, addr)) {
                fault(cpu, fault_mem_err);
            }

            // We got the address
            src = (uint64_t *) &cpu->memory[addr];
        } else {
            // It is just a memory op
            if (!is_valid_addr(cpu, instruction->data2)) {
                fault(cpu, fault_mem_err);
            }

            src = (uint64_t *) &cpu->memory[instruction->data2];
        }
    } else if (instruction->instruction_flags & INST_FLAG_SRC_CONST) {
        // Set src const, for garbage consistent interface for movement
        src_const = instruction->data2;
        src = &src_const;
    } else if (instruction->instruction_flags & INST_FLAG_SRC_REG) {
        // register move
        src = get_gpr(cpu, instruction->data2);
        if (!src) fault(cpu, fault_bad_reg);
    }

    /* Handle different dst cases */
    if (instruction->instruction_flags & INST_FLAG_DST_MEM_OP) {
        /* If the memory op is from a register */
        if (instruction->instruction_flags & INST_FLAG_DST_REG) {
            // It is a memory operation through a register
            uint64_t *reg = get_gpr(cpu, instruction->data1);
            if (!reg) {
                fault(cpu, fault_bad_reg);
            }

            uint64_t addr = *reg;
            if (!is_valid_addr(cpu, addr)) {
                fault(cpu, fault_mem_err);
            }

            // We got the address
            dst = (uint64_t *) &cpu->memory[addr];
        } else {
            // It is just a memory op
            if (!is_valid_addr(cpu, instruction->data1)) {
                fault(cpu, fault_mem_err);
            }

            dst = (uint64_t *) &cpu->memory[instruction->data1];
        }
    } else if (instruction->instruction_flags & INST_FLAG_DST_CONST) {
        printf("[LiquidCPU] Bad constant. Bruh moment\n");
        fault(cpu, fault_bad_flg);
    } else if (instruction->instruction_flags & INST_FLAG_DST_REG) {
        dst = get_gpr(cpu, instruction->data1);
        if (!dst) fault(cpu, fault_bad_reg);
    }

    *dst = *src;
}

/* jmp opcode */
void jmp_handler(cpu_t *cpu, instruction_t *instruction) {
    if (instruction->instruction_flags & INST_FLAG_DST_MEM_OP) {
        if (instruction->instruction_flags & INST_FLAG_DST_REG) {
            uint64_t *reg = get_gpr(cpu, instruction->data1);
            if (!reg) {
                fault(cpu, fault_bad_reg);
            }

            uint64_t addr = *reg;
            if (!is_valid_addr(cpu, addr)) {
                fault(cpu, fault_mem_err);
            }

            // We got the address
            cpu->ip = *(uint64_t *) &cpu->memory[addr];
        } else {
            if (!is_valid_addr(cpu, instruction->data1)) {
                fault(cpu, fault_mem_err);
            }

            cpu->ip = *(uint64_t *) &cpu->memory[instruction->data1];
        }
    } else if (instruction->instruction_flags & INST_FLAG_DST_CONST) {
        cpu->ip = instruction->data1;
    } else if (instruction->instruction_flags & INST_FLAG_DST_REG) {
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

void inc_handler(cpu_t *cpu, instruction_t *instruction) {
    if (instruction->instruction_flags & INST_FLAG_DST_MEM_OP) {
        if (instruction->instruction_flags & INST_FLAG_DST_REG) {
            uint64_t *reg = get_gpr(cpu, instruction->data1);
            if (!reg) {
                fault(cpu, fault_bad_reg);
            }

            uint64_t addr = *reg;
            if (!is_valid_addr(cpu, addr)) {
                fault(cpu, fault_mem_err);
            }

            // We got the address
            (*(uint64_t *) &cpu->memory[addr])++;
        } else {
            if (!is_valid_addr(cpu, instruction->data1)) {
                fault(cpu, fault_mem_err);
            }

            (*(uint64_t *) &cpu->memory[instruction->data1])++;
        }
    } else if (instruction->instruction_flags & INST_FLAG_DST_CONST) {
        printf("[LiquidCPU] Bad const. bruh\n");
        fault(cpu, fault_bad_flg);
    } else if (instruction->instruction_flags & INST_FLAG_DST_REG) {
        uint64_t *dst = get_gpr(cpu, instruction->data1);
        if (!dst) {
            fault(cpu, fault_bad_reg);
        }

        (*dst)++;
    }
}

void dec_handler(cpu_t *cpu, instruction_t *instruction) {
    if (instruction->instruction_flags & INST_FLAG_DST_MEM_OP) {
        if (instruction->instruction_flags & INST_FLAG_DST_REG) {
            uint64_t *reg = get_gpr(cpu, instruction->data1);
            if (!reg) {
                fault(cpu, fault_bad_reg);
            }

            uint64_t addr = *reg;
            if (!is_valid_addr(cpu, addr)) {
                fault(cpu, fault_mem_err);
            }

            // We got the address
            (*(uint64_t *) &cpu->memory[addr])--;
        } else {
            if (!is_valid_addr(cpu, instruction->data1)) {
                fault(cpu, fault_mem_err);
            }

            (*(uint64_t *) &cpu->memory[instruction->data1])--;
        }
    } else if (instruction->instruction_flags & INST_FLAG_DST_CONST) {
        printf("[LiquidCPU] Bad const. bruh\n");
        fault(cpu, fault_bad_flg);
    } else if (instruction->instruction_flags & INST_FLAG_DST_REG) {
        uint64_t *dst = get_gpr(cpu, instruction->data1);
        if (!dst) {
            fault(cpu, fault_bad_reg);
        }

        (*dst)--;
    }
}