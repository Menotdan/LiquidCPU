#ifndef LIQUID_CPU_H
#define LIQUID_CPU_H
#include <stdint.h>

#define MEMORY_SIZE 0x4000

typedef struct {
    /* GPRs */
    uint64_t r0;
    uint64_t r1;
    uint64_t r2;
    uint64_t r3;
    uint64_t r4;
    uint64_t r5;
    uint64_t r6;
    uint64_t r7;

    /* CPU used registers */
    uint64_t ip; // Instruction pointer
    uint64_t sp; // Stack pointer
    uint64_t flag; // Misc CPU flags

    /* CPU interrupt handler vector */
    uint64_t reg_int_vector; // The register that points to the interrupt table

    /* Memory area */
    uint8_t *memory;
    uint64_t memory_size;

    /* Clock cycles */
    uint64_t clock_cycles;
} cpu_t;

void setup_cpu(cpu_t *cpu);
void cpu_code_loop(cpu_t *cpu);
uint8_t is_valid_addr(cpu_t *cpu, uint64_t addr);
uint64_t get_operand_size(uint8_t operand_size);

#endif