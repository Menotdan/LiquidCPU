from struct import pack
import argparse
import time

INST_FLAG_DST_CONST = (1<<3)
INST_FLAG_DST_REG = (1<<5)

# Input stuff
verbose_level = 0

class liquidcpu_instruction:
    def __init__(self, opcode, instruction_flags, operand_sizes, data1, data2):
        self.instruction = opcode
        self.instruction_flags = instruction_flags
        self.operand_sizes = operand_sizes
        self.data1 = data1
        self.data2 = data2

def assembler_error(msg, line, filename):
    print("\nlasm: error!")
    print(msg)
    print("in file " + filename + ", on line " + str(line) + ".")
    quit()

def assembler_warn(msg, line, filename):
    print("Warning: " + str(msg))
    print("in file " + filename + ", on line " + str(line) + ".")

def assembler_log(msg):
    if verbose_level >= 1:
        print("[Info] " + str(msg))

def assembler_dbg(msg):
    if verbose_level >= 2:
        print("[Debug] " + str(msg))

def write_instruction(i, fp):
    assembler_dbg("Data " + str(i.instruction) + " " + str(i.instruction_flags) + " " + str(i.operand_sizes) + " " + str(i.data1) + " " + str(i.data2))
    fp.write(pack("<BBBQQ", i.instruction, i.instruction_flags, i.operand_sizes, i.data1, i.data2))

def tokenize(data):
    tokens = []
    string_storage = ""
    num_storage = ""
    last_was_num = False
    for line in data.split("\n"):
        for char in line:
            if char.isnumeric() and string_storage == "":
                # Number
                if last_was_num:
                    num_storage += char
                else:
                    num_storage = ""
                    num_storage += char
                last_was_num = True
            else:
                if last_was_num:
                    last_was_num = False
                    tokens.append(("number", int(num_storage)))
                # It is just a regular character
                if char == " ":
                    if string_storage != "":
                        tokens.append(("identifier", string_storage))

                    tokens.append(("space", char))
                    string_storage = ""
                elif char == ",":
                    if string_storage != "":
                        tokens.append(("identifier", string_storage))

                    tokens.append(("param_sep", char))
                    string_storage = ""
                elif char == ":":
                    if string_storage != "":
                        tokens.append(("identifier", string_storage))

                    tokens.append(("label_end", char))
                    string_storage = ""
                elif char == "\t":
                    if string_storage != "":
                        tokens.append(("identifier", string_storage))

                    tokens.append(("tab", char))
                    string_storage = ""
                else:
                    string_storage += char
        if last_was_num:
            tokens.append(("number", int(num_storage)))
            last_was_num = False
            num_storage = ""
        if string_storage != "":
            tokens.append(("identifier", string_storage))
            string_storage = ""
        
        # Add a newline
        tokens.append(("newline", "\n"))
    
    return tokens


# List of instructions for the assembler to parse
instruction_names = ["hlt", "jmp", "inc", "call", "ret"]
gprs              = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]
visible_regs      = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "ip", "sp"]

instruction_ops   = [2, 3, 4, 8, 9]
reg_indexes       = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

def get_opcode(name):
    return instruction_ops[instruction_names.index(name)]

def get_register_index(name):
    return reg_indexes[gprs.index(name)]

def parse_file(filename):
    global instruction_names

    ret_instructions = []

    fp = open(filename)
    data = fp.read()
    fp.close()
    
    tokens = tokenize(data)
    assembler_dbg(tokens)
    
    current_address = 0 # LiquidCPU code exec starts at 0
    labels = []
    last_identifier = ()

    line = 1

    token_index = 0
    skip_count = 0

    # Find all labels
    for token in tokens:
        if token[0] == "identifier":
            last_identifier = token
            if token[1] in instruction_names:
                # Increment by instruction size
                current_address += 19
        elif token[0] == "label_end":
            labels.append((last_identifier[1], current_address))
        elif token[0] == "newline":
            line += 1

    line = 0
    current_address = 0

    # Find all instructions and assemble them
    for token in tokens:
        assembler_dbg("Token: " + str(token))
        if skip_count > 0:
            skip_count -= 1
            token_index += 1
            continue

        if token[0] == "identifier":
            last_identifier = token
            if token[1] in instruction_names:
                # Found an instruction
                assembler_log("Found instruction " + token[1])
                instruction_name = token[1]

                # Get all the instruction tokens for this instruction
                instruction_tokens = []
                local_token_index = token_index + 1
                new_instruction = liquidcpu_instruction(0, 0, 0, 0, 0)
                while True:
                    if tokens[local_token_index][0] == "newline":
                        break
                    instruction_tokens.append(tokens[local_token_index])
                    local_token_index += 1
                skip_count = len(instruction_tokens)

                # Now that we have the instruction name and all it's tokens, do stuff
                if instruction_name == "jmp" or instruction_name == "call":
                    # Jump and call, because they share a similar signature
                    new_instruction.instruction = get_opcode(instruction_name)
                    handled_op = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] == "identifier":
                                # Check that we haven't already handled the identifier for this instruction
                                if handled_op:
                                    assembler_error("Stray " + instruction_token[0] + " after jmp", line, filename)

                                # Got the identifier
                                if any(instruction_token[1] in i for i in labels):
                                    # It is a label
                                    label = list(filter(lambda x:instruction_token[1] in x, labels))
                                    assembler_log("jmp using label " + instruction_token[1])
                                    new_instruction.data1 = label[0][1]
                                    new_instruction.instruction_flags = INST_FLAG_DST_CONST
                                    handled_op = True
                                elif instruction_token[1] in gprs:
                                    # It is a GPR
                                    assembler_log("jmp using gpr " + instruction_token[1])
                                    new_instruction.data1 = get_register_index(instruction_token[1])
                                    new_instruction.instruction_flags = INST_FLAG_DST_REG
                                    handled_op = True
                                else:
                                    assembler_error("Unknown jmp location " + instruction_token[1], line, filename)
                            elif instruction_token[0] == "number":
                                new_instruction.data1 = instruction_token[1]
                                new_instruction.instruction_flags = INST_FLAG_DST_CONST
                                assembler_log("jmp using const " + str(instruction_token[1]))
                            else:
                                if not handled_op:
                                    assembler_error("Expected identifier after jmp, got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after jmp", line, filename)
                            
                elif instruction_name == "hlt":
                    # Halt
                    if len(instruction_tokens) != 0:
                        assembler_error("Stray " + instruction_tokens[0][0] + " after hlt", line, filename)
                    new_instruction.instruction = get_opcode(instruction_name)
                elif instruction_name == "ret":
                    # Return
                    if len(instruction_tokens) != 0:
                        assembler_error("Stray " + instruction_tokens[0][0] + " after hlt", line, filename)
                    new_instruction.instruction = get_opcode(instruction_name)
                elif instruction_name == "inc":
                    # Increment
                    new_instruction.instruction = get_opcode(instruction_name)
                    handled_op = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] != "identifier":
                                if not handled_op:
                                    assembler_error("Expected identifier after inc, got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after inc", line, filename)
                            if handled_op:
                                assembler_error("Stray " + instruction_token[0] + " after inc", line, filename)

                            # Got the identifier
                            if instruction_token[1] in gprs:
                                # Found GPR
                                new_instruction.data1 = get_register_index(instruction_token[1])
                                new_instruction.instruction_flags = INST_FLAG_DST_REG
                            else:
                                assembler_error("Unknown inc operand " + instruction_token[1] + " in inc", line, filename)
                
                ### Parsed instruction ###

                # Increment by instruction size
                current_address += 19
                
                #Add instruction
                ret_instructions.append(new_instruction)
            else:
                if token_index + 1 < len(tokens):
                    if tokens[token_index + 1][0] == "label_end":
                        # Its a label
                        assembler_log("Found label " + token[1])
                    else:
                        assembler_error("Invalid instruction mnemonic " + token[1], line, filename)
                else:
                    assembler_error("Invalid instruction mnemonic " + token[1], line, filename)
        elif token[0] == "newline":
            line += 1
            tokens_since_newline = False
        token_index += 1

    return ret_instructions

def main():
    global verbose_level

    parser = argparse.ArgumentParser(description='Assemble a LiquidCPU assembly program.')
    parser.add_argument('--output', '-o')
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('inputs', nargs='*')
    result = parser.parse_args()
    
    if len(result.inputs) == 0:
        print("usage error!")
        parser.print_usage()
        quit()
    
    if result.verbose:
        verbose_level = result.verbose

    start = time.time()

    instruction_list = []
    for input_file in result.inputs:
        output = parse_file(input_file)
        for outputs in output:
            instruction_list.append(outputs)

    end = time.time()

    if result.output:
        with open(result.output, "wb") as file:
            for instruction in instruction_list:
                write_instruction(instruction, file)
    else:
        with open("lasm.liq", "wb") as file:
            for instruction in instruction_list:
                write_instruction(instruction, file)
    
    print("Assembled in " + str(end - start) + " seconds.")

main()