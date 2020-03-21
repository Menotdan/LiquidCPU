#ifndef LIQUID_MICROCODE_H
#define LIQUID_MICROCODE_H
#include <stdint.h>

#define INST_FLAG_SRC_MEM_OP (1<<0)
#define INST_FLAG_DST_MEM_OP (1<<1)
#define INST_FLAG_SRC_CONST (1<<2)
#define INST_FLAG_DST_CONST (1<<3)

#define CPU_FLAG_HLT (1<<0)

enum REGISTERS {
    /* GPRs */
    reg_r0,
    reg_r1,
    reg_r2,
    reg_r3,
    reg_r4,
    reg_r5,
    reg_r6,
    reg_r7,
    
    /* CPU registers */
    reg_ip,
    reg_sp,
    reg_flag,

    reg_int_vector_ptr,
};

enum FAULTS {
    fault_invl_opcode,
    fault_bad_reg,
};

enum INSTRUCTIONS {
    instruction_mov,
    instruction_hlt,
};

typedef struct {
    uint64_t instruction;
    uint64_t instruction_flags;
    uint64_t data1;
    uint64_t data2;
} instruction_t;

#endif