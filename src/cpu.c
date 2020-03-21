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
            default:
                printf("[LiquidCPU] Bad instruction %lx\n", instruction->instruction);
                fault(cpu, fault_invl_opcode);
                break;
        }
        printf("[LiquidCPU] r0: 0x%lx\n", cpu->r0);
    }
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