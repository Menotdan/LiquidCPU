#ifndef LIQUID_OPCODE_HANDLERS_H
#define LIQUID_OPCODE_HANDLERS_H
#include <stdint.h>
#include "microcode.h"
#include "cpu.h"

/* Instructions */
void move_handler(cpu_t *cpu, instruction_t *instruction);
void hlt_handler(cpu_t *cpu, instruction_t *instruction);
void jmp_handler(cpu_t *cpu, instruction_t *instruction);
void inc_handler(cpu_t *cpu, instruction_t *instruction);
void dec_handler(cpu_t *cpu, instruction_t *instruction);
void push_handler(cpu_t *cpu, instruction_t *instruction);
void pop_handler(cpu_t *cpu, instruction_t *instruction);
void call_handler(cpu_t *cpu, instruction_t *instruction);
void ret_handler(cpu_t *cpu, instruction_t *instruction);

/* Fault stuff */
void fault(cpu_t *cpu, uint64_t fault_no);

#endif