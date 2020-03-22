#include "cpu.h"
#include <stdio.h>
#include <stdlib.h>
#include "microcode/microcode.h"
#include "microcode/opcode_handlers.h"

uint8_t is_valid_addr(cpu_t *cpu, uint64_t addr) {
    if (addr > cpu->memory_size) {
        return 0;
    }

    return 1;
}

uint64_t get_operand_size(uint8_t operand_size) {
    switch (operand_size) {
        case operand_1:
            return 1;
            break;
        case operand_2:
            return 2;
            break;
        case operand_4:
            return 4;
            break;
        case operand_8:
            return 8;
            break;
        case operand_16:
            return 16;
            break;
        case operand_24:
            return 24;
            break;
        case operand_32:
            return 32;
            break;
        case operand_40:
            return 40;
            break;
        case operand_48:
            return 48;
            break;
        case operand_56:
            return 56;
            break;
        case operand_64:
            return 64;
            break;
        case operand_128:
            return 128;
            break;
        case operand_256:
            return 256;
            break;
        case operand_512:
            return 512;
            break;
        case operand_1024:
            return 1024;
            break;
        case operand_2048:
            return 2048;
            break;
        default:
            return 0;
            break;
    }
}

uint64_t clock_cycles = 0;

void execute_instruction(cpu_t *cpu) {
    instruction_t *instruction = (instruction_t *) &cpu->memory[cpu->ip];

    if (!(cpu->flag & CPU_FLAG_HLT)) {
        printf("[LiquidCPU] Got instruction 0x%lx\n", instruction->instruction);

        /* Memory check */
        if (!is_valid_addr(cpu, cpu->ip + sizeof(instruction_t) - 1)) {
            fault(cpu, fault_mem_err); // Memory access check
        }
        cpu->ip += sizeof(instruction_t); // Modify the IP before executing, so that jmp, etc. works

        switch (instruction->instruction) {
            case instruction_nop:
                break;
            case instruction_mov:
                move_handler(cpu, instruction);
                break;
            case instruction_hlt:
                hlt_handler(cpu, instruction);
                printf("[LiquidCPU] Halted.\n");
                break;
            case instruction_jmp:
                jmp_handler(cpu, instruction);
                break;
            case instruction_inc:
                inc_handler(cpu, instruction);
                break;
            case instruction_dec:
                dec_handler(cpu, instruction);
                break;
            case instruction_push:
                push_handler(cpu, instruction);
                break;
            case instruction_pop:
                pop_handler(cpu, instruction);
                break;
            case instruction_call:
                call_handler(cpu, instruction);
                break;
            case instruction_ret:
                ret_handler(cpu, instruction);
                break;
            default:
                printf("[LiquidCPU] Bad instruction %lx\n", instruction->instruction);
                fault(cpu, fault_invl_opcode);
                break;
        }
        //printf("[LiquidCPU] r0: 0x%lx\n[LiquidCPU] r1: 0x%lx\n", cpu->r0, cpu->r1);
    }

    clock_cycles++;
    // if (clock_cycles % 1000000 == 0) {
    //     printf("[LiquidCPU] r0: 0x%lx\n[LiquidCPU] r1: 0x%lx\n[LiquidCPU] ip: 0x%lx\n", cpu->r0, cpu->r1, cpu->ip);
    //     printf("[LiquidCPU] clock_cycles: %lu\n", clock_cycles);
    // }
}

void setup_cpu_mem(cpu_t *cpu) {
    cpu->memory = calloc(MEMORY_SIZE, 1);
    cpu->memory_size = MEMORY_SIZE;
}

void setup_cpu(cpu_t *cpu) {
    cpu->ip = 0x0;    // LiquidCPU starts executing at addr 0
    cpu->sp = 0x1000; // The stack starts at 0x1000, but should be changed by the user
    cpu->flag = 0x0; // No CPU flags should be set
    
    cpu->reg_int_vector = 0; // The CPU won't execute interrupt vectors, such as faults if this register is 0
    
    /* Clear all GPRs */
    cpu->r0 = 0;
    cpu->r1 = 0;
    cpu->r2 = 0;
    cpu->r3 = 0;
    cpu->r4 = 0;
    cpu->r5 = 0;
    cpu->r6 = 0;
    cpu->r7 = 0;

    /* Set up CPU's memory area */
    setup_cpu_mem(cpu);
}

void cpu_code_loop(cpu_t *cpu) {
    while (1) {
        execute_instruction(cpu);
    }
}