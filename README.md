# LiquidCPU
A simple ISA written and emulated in C (I think).

## Dependencies:
- python 3+
- gcc

## Instructions:
This repo has two parts. Part 1 is the assembler, which is written in Python. You can run the assembler by running `python assembler.py -o output_file.liq input_file.lasm`, which will assemble `input_file.lasm` into `output_file.liq`, an "executable" file for the LiquidCPU.

Part 2 of this repo is the CPU executable itself (requires `gcc` to build). You can build it by simply running `make`. You can then execute the previously assembled executable using `./liquid_cpu output_file.liq`.

## Assembly code:
| Instruction Name | Opcode | Description | Usage |
|------------------|--------|-------------|--------|
| `nop`  | 0 | Performs no operation. | `nop` |
| `mov`  | 1 | Moves data from `src` to `dst`. | `mov dst, src` |
| `hlt`  | 2 | Halts execution. | `hlt` |
| `jmp`  | 3 | Changes the instruction pointer to the specified address. | `jmp addr` |
| `inc`  | 4 | Increments the number at the target location by 1. | `inc target` |
| `dec`  | 5 | Decrements the number at the target location by 1. | `dec target` |
| `push` | 6 | Pushes the data to the stack. | `push data` |
| `pop`  | 7 | Pops the most recent data off the stack and stores it at the target address. | `pop target` |
| `call` | 8 | Pushes current instruction pointer to the stack, and then changes the instruction pointer to the specified address. | `call addr` |
| `ret`  | 9 | Pops the most recent data off the stack and stores it in the instruction pointer. | `ret` |
