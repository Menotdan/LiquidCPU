from struct import pack
import argparse
import time

INST_FLAG_SRC_MEM_OP = (1<<0)
INST_FLAG_DST_MEM_OP = (1<<1)
INST_FLAG_SRC_CONST  = (1<<2)
INST_FLAG_DST_CONST  = (1<<3)
INST_FLAG_SRC_REG    = (1<<4)
INST_FLAG_DST_REG    = (1<<5)

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

def write_data(i, fp):
    assembler_dbg("Data " + str(i[0]))

    if i[1] == 8:
        fp.write(pack("<Q", i[0]))

def tokenize(data, filename):
    tokens = []
    string_storage = ""
    num_storage = ""
    last_was_num = False
    bracket_open = False

    line_num = 1

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
                elif char == "[":
                    if string_storage != "":
                        tokens.append(("identifier", string_storage))

                    tokens.append(("bracket_open", char))
                    string_storage = ""

                    if bracket_open:
                        assembler_error("Opening an already open bracket!", line_num, filename)

                    bracket_open = True
                elif char == "]":
                    if string_storage != "":
                        tokens.append(("identifier", string_storage))

                    tokens.append(("bracket_close", char))
                    string_storage = ""

                    if not bracket_open:
                        assembler_error("Closing an already closed bracket!", line_num, filename)

                    bracket_open = False
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
        if bracket_open:
            assembler_error("Bracket left opened!", line_num, filename)
        line_num += 1
    
    return tokens


# List of instructions for the assembler to parse
instruction_names = ["nop", "mov", "hlt", "jmp", "inc", "dec", "push", "pop", "call", "ret"]
assembler_macros  = ["dq"]
gprs              = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]
visible_regs      = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "ip", "sp"]

instruction_ops   = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
reg_indexes       = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

def get_opcode(name):
    return instruction_ops[instruction_names.index(name)]

def get_register_index(name):
    return reg_indexes[gprs.index(name)]

def parse_file(filename):
    global instruction_names

    ret_instructions = []

    with open(filename) as fp:
        data = fp.read()
    
    tokens = tokenize(data, filename)
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
            elif token[1] in assembler_macros:
                if token[1] == "dq":
                    current_address += 8
        elif token[0] == "label_end":
            labels.append((last_identifier[1], current_address))
        elif token[0] == "newline":
            line += 1

    line = 1
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
                    in_bracket = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] == "identifier":
                                # Check that we haven't already handled the identifier for this instruction
                                if handled_op:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                                # Got the identifier
                                if any(instruction_token[1] in i for i in labels):
                                    # It is a label
                                    label = list(filter(lambda x:instruction_token[1] in x, labels))
                                    if not in_bracket:
                                        assembler_log(instruction_name + " using label " + instruction_token[1])
                                        new_instruction.data1 = label[0][1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_CONST
                                    else:
                                        assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                        new_instruction.data1 = label[0][1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP

                                    handled_op = True
                                elif instruction_token[1] in gprs:
                                    if not in_bracket:
                                        # It is a GPR
                                        assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                        new_instruction.data1 = get_register_index(instruction_token[1])
                                        new_instruction.instruction_flags |= INST_FLAG_DST_REG
                                    else:
                                        assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                        new_instruction.data1 = get_register_index(instruction_token[1])
                                        
                                        # Memory op and register in 1
                                        new_instruction.instruction_flags |= INST_FLAG_DST_REG | INST_FLAG_DST_MEM_OP

                                    handled_op = True
                                else:
                                    assembler_error("Unknown " + instruction_name + " operand " + instruction_token[1], line, filename)
                            elif instruction_token[0] == "number":
                                if not in_bracket:
                                    new_instruction.data1 = instruction_token[1]
                                    new_instruction.instruction_flags |= INST_FLAG_DST_CONST
                                    assembler_log(instruction_name + " using const " + str(instruction_token[1]))
                                else:
                                    new_instruction.data1 = instruction_token[1]
                                    new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP
                                    assembler_log(instruction_name + " using const mem " + str(instruction_token[1]))

                                handled_op = True
                            elif instruction_token[0] == "bracket_open":
                                in_bracket = True
                                if handled_op:
                                    assembler_error("Stray open bracket!", line, filename)
                            elif instruction_token[0] == "bracket_close":
                                in_bracket = False
                            else:
                                if not handled_op:
                                    assembler_error("Expected identifier, number, or bracket after " + instruction_name + ", got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                elif instruction_name == "push":
                    # Push
                    new_instruction.instruction = get_opcode(instruction_name)
                    handled_op = False
                    in_bracket = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] == "identifier":
                                # Check that we haven't already handled the identifier for this instruction
                                if handled_op:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                                # Got the identifier
                                if any(instruction_token[1] in i for i in labels):
                                    # It is a label
                                    label = list(filter(lambda x:instruction_token[1] in x, labels))
                                    if not in_bracket:
                                        assembler_log(instruction_name + " using label " + instruction_token[1])
                                        new_instruction.data1 = label[0][1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_CONST
                                    else:
                                        assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                        new_instruction.data1 = label[0][1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP
                                elif instruction_token[1] in gprs:
                                    # It is a GPR
                                    if not in_bracket:
                                        # Not memory operand
                                        assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                        new_instruction.data1 = get_register_index(instruction_token[1])
                                        new_instruction.instruction_flags |= INST_FLAG_DST_REG
                                    else:
                                        # Memory operand
                                        assembler_log(instruction_name + " using gpr mem " + instruction_token[1])
                                        new_instruction.data1 = get_register_index(instruction_token[1])
                                        new_instruction.instruction_flags |= INST_FLAG_DST_REG | INST_FLAG_DST_MEM_OP

                                    handled_op = True
                                else:
                                    assembler_error("Unknown " + instruction_name + " operand " + instruction_token[1], line, filename)
                            elif instruction_token[0] == "number":
                                # Not memory operand
                                if not in_bracket:
                                    new_instruction.data1 = instruction_token[1]
                                    new_instruction.instruction_flags |= INST_FLAG_DST_CONST
                                    assembler_log(instruction_name + " using const " + str(instruction_token[1]))
                                # Is memory operand
                                else:
                                    new_instruction.data1 = instruction_token[1]
                                    new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP
                                    assembler_log(instruction_name + " using const mem " + str(instruction_token[1]))

                                handled_op = True
                            elif instruction_token[0] == "bracket_open":
                                in_bracket = True
                                if handled_op:
                                    assembler_error("Stray open bracket!", line, filename)
                            elif instruction_token[0] == "bracket_close":
                                in_bracket = False
                            else:
                                if not handled_op:
                                    assembler_error("Expected identifier or number after " + instruction_name + ", got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                elif instruction_name == "pop":
                    # Pop
                    new_instruction.instruction = get_opcode(instruction_name)
                    handled_op = False
                    in_bracket = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] == "identifier":
                                # Check that we haven't already handled the identifier for this instruction
                                if handled_op:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                                # Got the identifier
                                if any(instruction_token[1] in i for i in labels):
                                    # It is a label
                                    label = list(filter(lambda x:instruction_token[1] in x, labels))
                                    if not in_bracket:
                                        assembler_error("Cannot pop into a constant label address!", line, filename)
                                    else:
                                        assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                        new_instruction.data1 = label[0][1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP
                                elif instruction_token[1] in gprs:
                                    # It is a GPR

                                    # Is memory operand
                                    if not in_bracket:
                                        assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                        new_instruction.data1 = get_register_index(instruction_token[1])
                                        new_instruction.instruction_flags |= INST_FLAG_DST_REG
                                    # Is not memory operand
                                    else:
                                        assembler_log(instruction_name + " using gpr mem " + instruction_token[1])
                                        new_instruction.data1 = get_register_index(instruction_token[1])
                                        new_instruction.instruction_flags |= INST_FLAG_DST_REG | INST_FLAG_DST_MEM_OP

                                    handled_op = True
                                else:
                                    assembler_error("Unknown " + instruction_name + " operand " + instruction_token[1], line, filename)
                            elif instruction_token[0] == "number":
                                # Cannot pop into constants lol
                                if not in_bracket:
                                    assembler_error("Cannot pop into constant!", line, filename)
                                # Memory addr constant
                                else:
                                    assembler_log(instruction_name + " using mem const " + str(instruction_token[1]))
                                    new_instruction.data1 = get_register_index(instruction_token[1])
                                    new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP

                            elif instruction_token[0] == "bracket_open":
                                in_bracket = True
                                if handled_op:
                                    assembler_error("Stray open bracket!", line, filename)
                            elif instruction_token[0] == "bracket_close":
                                in_bracket = False
                            else:
                                if not handled_op:
                                    assembler_error("Expected identifier after " + instruction_name + ", got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                elif instruction_name == "hlt":
                    # Halt
                    if len(instruction_tokens) != 0:
                        assembler_error("Stray " + instruction_tokens[0][0] + " after " + instruction_name, line, filename)
                    new_instruction.instruction = get_opcode(instruction_name)

                elif instruction_name == "nop":
                    # Halt
                    if len(instruction_tokens) != 0:
                        assembler_error("Stray " + instruction_tokens[0][0] + " after " + instruction_name, line, filename)
                    new_instruction.instruction = get_opcode(instruction_name)

                elif instruction_name == "ret":
                    # Return
                    if len(instruction_tokens) != 0:
                        assembler_error("Stray " + instruction_tokens[0][0] + " after " + instruction_name, line, filename)
                    new_instruction.instruction = get_opcode(instruction_name)

                elif instruction_name == "inc" or instruction_name == "dec":
                    # Increment
                    new_instruction.instruction = get_opcode(instruction_name)
                    handled_op = False
                    in_bracket = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] != "identifier":
                                if not handled_op:
                                    assembler_error("Expected identifier after " + instruction_name + ", got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)
                            if handled_op:
                                assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                            # Got the identifier

                            if any(instruction_token[1] in i for i in labels):
                                    # It is a label
                                    label = list(filter(lambda x:instruction_token[1] in x, labels))
                                    if not in_bracket:
                                        assembler_error("Cannot " + instruction_name + " into a constant label address!", line, filename)
                                    else:
                                        assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                        new_instruction.data1 = label[0][1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP
                            elif instruction_token[1] in gprs:
                                # Found GPR
                                if not in_bracket:
                                    new_instruction.data1 = get_register_index(instruction_token[1])
                                    new_instruction.instruction_flags |= INST_FLAG_DST_REG
                                else:
                                    new_instruction.data1 = get_register_index(instruction_token[1])
                                    new_instruction.instruction_flags |= INST_FLAG_DST_REG | INST_FLAG_DST_MEM_OP

                                handled_op = True
                            elif instruction_token[0] == "number":
                                if not in_bracket:
                                    assembler_error("Cannot use " + instruction_name + " on a constant!", line, filename)
                                else:
                                    assembler_log(instruction_name + " using mem const " + str(instruction_token[1]))
                                    new_instruction.data1 = get_register_index(instruction_token[1])
                                    new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP

                            elif instruction_token[0] == "bracket_open":
                                in_bracket = True
                                if handled_op:
                                    assembler_error("Stray open bracket!", line, filename)
                            elif instruction_token[0] == "bracket_close":
                                in_bracket = False
                            else:
                                assembler_error("Unknown " + instruction_name + " operand " + instruction_token[1], line, filename)

                elif instruction_name == "mov":
                    # Jump and call, because they share a similar signature
                    new_instruction.instruction = get_opcode(instruction_name)
                    handled_operands = 0
                    handled_comma = False
                    in_bracket = False

                    # Look for the correct formatting with the jmp instruction
                    for instruction_token in instruction_tokens:
                        if instruction_token[0] != "space":
                            if instruction_token[0] == "identifier":
                                # Check that we haven't already handled the identifiers for this instruction
                                if handled_operands == 2:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)

                                # Got the identifier
                                if any(instruction_token[1] in i for i in labels):
                                    # It is a label
                                    label = list(filter(lambda x:instruction_token[1] in x, labels))
                                    if not in_bracket:
                                        if handled_operands == 0:
                                            assembler_error("Cannot " + instruction_name + " into a constant label address!", line, filename)

                                        elif handled_operands == 1:
                                            if not handled_comma:
                                                assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)
                                            assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                            new_instruction.data2 = label[0][1]
                                            new_instruction.instruction_flags |= INST_FLAG_SRC_CONST
                                    else:
                                        if handled_operands == 0:
                                            assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                            new_instruction.data1 = label[0][1]
                                            new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP

                                        elif handled_operands == 1:
                                            if not handled_comma:
                                                assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)

                                            assembler_log(instruction_name + " using label mem " + instruction_token[1])
                                            new_instruction.data2 = label[0][1]
                                            new_instruction.instruction_flags |= INST_FLAG_SRC_MEM_OP
                                elif instruction_token[1] in gprs:
                                    # It is a GPR

                                    if not in_bracket:
                                        if handled_operands == 0:
                                            assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                            new_instruction.data1 = get_register_index(instruction_token[1])
                                            new_instruction.instruction_flags |= INST_FLAG_DST_REG
                                        elif handled_operands == 1:
                                            if not handled_comma:
                                                assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)

                                            assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                            new_instruction.data2 = get_register_index(instruction_token[1])
                                            new_instruction.instruction_flags |= INST_FLAG_SRC_REG
                                    else:
                                        if handled_operands == 0:
                                            assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                            new_instruction.data1 = get_register_index(instruction_token[1])
                                            new_instruction.instruction_flags |= INST_FLAG_DST_REG | INST_FLAG_DST_MEM_OP
                                        elif handled_operands == 1:
                                            if not handled_comma:
                                                assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)

                                            assembler_log(instruction_name + " using gpr " + instruction_token[1])
                                            new_instruction.data2 = get_register_index(instruction_token[1])
                                            new_instruction.instruction_flags |= INST_FLAG_SRC_REG | INST_FLAG_DST_MEM_OP

                                    handled_operands += 1
                                else:
                                    assembler_error("Unknown " + instruction_name + " operand " + instruction_token[1], line, filename)
                            elif instruction_token[0] == "number":
                                if handled_operands >= 2:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name + "!", line, filename)

                                if not in_bracket:
                                    if handled_operands == 0:
                                        assembler_error(instruction_name + " cannot have constant destination!", line, filename)
                                    elif handled_operands == 1:
                                        if not handled_comma:
                                            assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)

                                        new_instruction.data2 = instruction_token[1]
                                        new_instruction.instruction_flags |= INST_FLAG_SRC_CONST
                                        assembler_log(instruction_name + " using const " + str(instruction_token[1]))

                                        handled_operands += 1

                                else:
                                    if handled_operands == 0:
                                        new_instruction.data1 = instruction_token[1]
                                        new_instruction.instruction_flags |= INST_FLAG_DST_MEM_OP
                                        assembler_log(instruction_name + " using const mem " + str(instruction_token[1]))

                                        handled_operands += 1
                                    elif handled_operands == 1:
                                        if not handled_comma:
                                            assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)

                                        new_instruction.data2 = instruction_token[1]
                                        new_instruction.instruction_flags |= INST_FLAG_SRC_MEM_OP
                                        assembler_log(instruction_name + " using const mem " + str(instruction_token[1]))

                                        handled_operands += 1

                            elif instruction_token[0] == "param_sep":
                                # Comma
                                if handled_comma:
                                    assembler_error("Stray comma after " + instruction_name + "!", line, filename)
                                handled_comma = True

                            elif instruction_token[0] == "bracket_open":
                                # If we dont have a comma yet
                                if handled_operands == 1 and not handled_comma:
                                    assembler_error("Missing comma for operand 2 of " + instruction_name + "!", line, filename)
                                in_bracket = True

                                # If we already handled the operands
                                if handled_operands == 2:
                                    assembler_error("Stray open bracket!", line, filename)
                            elif instruction_token[0] == "bracket_close":
                                in_bracket = False
                            else:
                                if handled_op != 2:
                                    assembler_error("Expected identifier after " + instruction_name + ", got " + instruction_token[0], line, filename)
                                else:
                                    assembler_error("Stray " + instruction_token[0] + " after " + instruction_name, line, filename)
                    if handled_operands > 2:
                        assembler_error("Handled operands is > 2!", line, filename)
                ### Parsed instruction ###

                # Increment by instruction size
                current_address += 19
                
                #Add instruction
                ret_instructions.append(("instruction", new_instruction, 19))

            elif token[1] in assembler_macros:
                mnemonic_name = token[1]
                # Get all the instruction tokens for this instruction
                mnemonic_tokens = []
                local_token_index = token_index + 1
                while True:
                    if tokens[local_token_index][0] == "newline":
                        break
                    mnemonic_tokens.append(tokens[local_token_index])
                    local_token_index += 1
                skip_count = len(mnemonic_tokens)

                if mnemonic_name == "dq":
                    handled_op = False

                    for mnemonic_token in mnemonic_tokens:
                        if mnemonic_token[0] != "space":
                            if mnemonic_token[0] != "number":
                                assembler_error("Expected number, got " + mnemonic_token[0] + "!", line, filename)
                            if handled_op:
                                assembler_error("Stray " + mnemonic_token[0] + " after " + mnemonic_name + "!", line, filename)
                            # Is a number
                            data_to_add = mnemonic_token[1]
                            ret_instructions.append(("data", data_to_add, 8))
                            current_address += 8 # Add the dq size to the current address
                            handled_op = True

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

    instruction_data_list = []
    for input_file in result.inputs:
        output = parse_file(input_file)
        for outputs in output:
            instruction_data_list.append(outputs)

    end = time.time()

    if result.output:
        with open(result.output, "wb") as file:
            for instruction in instruction_data_list:
                if instruction[0] == "instruction":
                    write_instruction(instruction[1], file)
                elif instruction[0] == "data":
                    write_data((instruction[1], instruction[2]), file)
    else:
        with open("lasm.liq", "wb") as file:
            for instruction in instruction_data_list:
                if instruction[0] == "instruction":
                    write_instruction(instruction[1], file)
                elif instruction[0] == "data":
                    write_data((instruction[1], instruction[2]), file)
    
    print("Assembled in " + str(end - start) + " seconds.")

main()