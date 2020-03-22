#ifndef LIQUID_MICROCODE_H
#define LIQUID_MICROCODE_H
#include <stdint.h>

#define INST_FLAG_SRC_MEM_OP (1<<0)
#define INST_FLAG_DST_MEM_OP (1<<1)
#define INST_FLAG_SRC_CONST (1<<2)
#define INST_FLAG_DST_CONST (1<<3)
#define INST_FLAG_SRC_REG (1<<4)
#define INST_FLAG_DST_REG (1<<5)

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
    fault_mem_err,
    fault_bad_flg,
};

enum INSTRUCTIONS {
    instruction_nop,
    instruction_mov,
    instruction_hlt,
    instruction_jmp,
    instruction_inc,
    instruction_dec,
    instruction_push,
    instruction_pop,
    instruction_call,
    instruction_ret,
};

enum OPERAND_SIZES {
    operand_1,
    operand_2,
    operand_4,
    operand_8,
    operand_16,
    operand_24,
    operand_32,
    operand_40,
    operand_48,
    operand_56,
    operand_64,
    operand_128,
    operand_256,
    operand_512,
    operand_1024,
    operand_2048,
};

typedef struct {
    uint8_t instruction;
    uint8_t instruction_flags;
    uint8_t operand_size_src : 4;
    uint8_t operand_size_dst : 4;
    uint64_t data1;
    uint64_t data2;
} __attribute__((packed)) instruction_t;

#endif