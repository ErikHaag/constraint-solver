from data_classes import *
from wrapper_classes import *
from dataclasses import asdict
import json
import math
import random
import statistics
import sys
from typing import Literal

class InsuffientArguments(ArithmeticError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

variables : dict[str, str] = {}

def convert_if_valid_float(potentialFloat:str) -> tuple[bool, float]:
        try:
            v = float(potentialFloat)
            return (True, v)
        except ValueError:
            return (False, 0.0)

def evaluate_expression(expr:str, dependent:dict[str, float] = {}, max_substitutions = 1000) -> str:
    stack : list[float] = []
    commands : list[str] = [i for i in expr.strip().split(" ")]
    out_commands : list[str] = []

    substitution_count = 0

    while len(commands) > 0:
        c = commands.pop(0)
        
        try:
            match c:
                case "+":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b + a)
                case "-":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b - a)
                case "_":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.append(-stack.pop())
                case "*":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b * a)
                case "/":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b / a)
                case "//":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b // a)
                case "%":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b % a)
                case "**":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b ** a)
                case "atan":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(math.atan2(a, b))
                case "choice":
                    if len(commands) < 2:
                        raise RuntimeError()
                    if len (stack) < 1:
                        raise InsuffientArguments()
                    if stack.pop() == 0:
                        commands.pop(0)
                    else:
                        commands.pop(1)
                case "cos":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.append(math.cos(stack.pop()))
                case "compare":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    a = stack.pop()
                    b = stack.pop()
                    if b > a:
                        stack.append(1)
                    elif b < a:
                        stack.append(-1)
                    else:
                        stack.append(0)
                case "drop":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.pop()
                case "dup":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.append(stack[-1])
                case "sin":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.append(math.sin(stack.pop()))
                case "sqrt":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.append(math.sqrt(stack.pop()))
                case "step":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    stack.append(1 if stack.pop() > 0 else 0)
                case "nop":
                    pass
                case "pull":
                    if len(stack) < 1:
                        raise InsuffientArguments()
                    i = int(stack.pop())
                    if len(stack) <= i:
                        stack.append(i)
                        raise InsuffientArguments()
                    stack.append(stack.pop(~i))
                case "push":
                    if len(stack) < 2:
                        raise InsuffientArguments()
                    i = int(stack.pop())
                    v = stack.pop()
                    if len(stack) < i:
                        stack.append(v)
                        stack.append(i)
                        raise InsuffientArguments()
                    if i == 0:
                        stack.append(v)
                    else:
                        stack.insert(-i, v)
                case _:
                    (s, v) = convert_if_valid_float(c)
                    var_exp = variables.get(c)
                    dep_exp = dependent.get(c)
                    if s:
                        stack.append(v)
                    elif dep_exp != None:
                        stack.append(dep_exp)
                    elif var_exp != None:
                        if substitution_count >= max_substitutions:
                            raise RecursionError()
                        commands = [j for i in [var_exp.strip().split(" "), commands] for j in i]
                        substitution_count += 1
                    else:
                        raise NameError("Unknown variable or expression \"" + c + "\"")
        except InsuffientArguments:
            out_commands.extend([str(i) for i in stack])
            stack.clear()
            out_commands.append(c)
            if c == "choice":
                out_commands.append(commands.pop(0))
                out_commands.append(commands.pop(0))
    out_commands.extend([str(i) for i in stack])
    return " ".join(out_commands)


def load_previous_solution(constraint:constraint_model) -> tuple[bool, list[float]]:
    for cons in old_dependency_data:
        if len(cons.constraint.variables) != len(constraint.variables)\
            or len(cons.constraint.assertions) != len(constraint.assertions)\
            or len(cons.constraint.restrictions) != len(constraint.restrictions):
            continue
        if any([s != c for (s, c) in zip(cons.constraint.variables, constraint.variables)])\
            or any([s != c for (s, c) in zip(cons.constraint.assertions, constraint.assertions)])\
            or any([s != c for (s, c) in zip(cons.constraint.restrictions, constraint.restrictions)]):
            continue
        if any([k not in variables or variables[k] != v for k, v in cons.dependentVariables.items()]):
            continue
        return (True, cons.evaluations)
    return (False, [])


# -1 -> a > b
# 0 -> a == b
# 1 -> a < b
def compare_constraint_sets(a:constraint_result, b:constraint_result) -> Literal[-1, 0, 1]:
    if a.success_count < b.success_count:
        return -1
    if a.success_count > b.success_count:
        return 1
            
    if a.success_count >= 1:
        if a.restriction_result < b.restriction_result:
            return 1
        if a.restriction_result > b.restriction_result:
            return -1

    if a.assertion_result < b.assertion_result:
        return 1
    if a.assertion_result > b.assertion_result:
        return -1
    return 0

def evaluate_constraint_set(constraint:constraint_model, var_set:list[float]) -> constraint_result:
    d = dict(zip(constraint.variables, var_set))
    restriction_result = 0
    for assertion in constraint.restrictions:
        try:
            o = evaluate_expression(assertion, d)
        except ArithmeticError, RecursionError, ValueError, ZeroDivisionError:
            # failure
            return constraint_result(0, 0, 0)
        (s, f) = convert_if_valid_float(o)
        if not s:
            raise RuntimeError(f"Evaluation of the following assertion resulted in an expression\n{assertion}\n" + "\n".join([f"{k} >> {v}" for [k,v] in zip(constraint.variables, var_set)]) + f"\n\n-> {o}")
        restriction_result += 0 if f <= 0 else f
    assertion_result = 0
    for assertion in constraint.assertions:
        try:
            o = evaluate_expression(assertion, d)
        except ArithmeticError, RecursionError, ValueError, ZeroDivisionError:
            # failure
            return constraint_result(1, restriction_result, 0)
        (s, f) = convert_if_valid_float(o)
        if not s:
            raise RuntimeError(f"Evaluation of the following assertion resulted in an expression\n{assertion}\n" + "\n".join([f"{k} >> {v}" for [k,v] in zip(constraint.variables, var_set)]) + f"\n\n-> {o}")
        assertion_result += f ** 2
    return constraint_result(2, restriction_result, assertion_result)

def sort_evaluations(eval_list:list[constraint_result], mirror:list)->tuple[list[constraint_result], list]:
    if len(eval_list) != len(mirror):
        raise Exception()
    for i in range(len(eval_list) - 1):
        minJ = i
        for j in range(i + 1, len(eval_list)):
            if compare_constraint_sets(eval_list[minJ], eval_list[j]) == -1:
                minJ = j        
        if minJ != i:
            (eval_list[i], eval_list[minJ]) = (eval_list[minJ], eval_list[i])
            (mirror[i], mirror[minJ]) = (mirror[minJ], mirror[i])
    return (eval_list, mirror)

def get_dependent_expressions(exprs:list[str], dependent_vars:list[str]) -> dict[str, str]:
    output_dict:dict[str,str] = dict()
    while len(exprs) > 0:
        current_expr = exprs.pop()
        for command in current_expr.split(" "):
            command = command.strip()
            if len(command) == 0:
                continue
            if command in output_dict:
                continue
            if command in ["+", "-", "_", "*", "/", "//", "%", "**", "atan", "choice", "cos", "compare", "drop", "dup", "sin", "sqrt", "step", "nop", "pull", "push"]:
                continue
            if convert_if_valid_float(command)[0]:
                continue
            if command in dependent_vars:
                continue
            if command not in variables:
                raise Exception(f"Found unknown variable \"{command}\"")
            subExp = variables[command]
            output_dict[command] = subExp
            exprs.append(subExp)
    return output_dict

data : input_data_model

with open(sys.argv[1] if len(sys.argv) == 2 else "constraint_input.json", "r") as f:
    data = input_data_model.from_dict(json.loads("\n".join(f.readlines())))

dumping = data.dump != ""

definition_iterator = iter(data.definitions)
constraint_iterator = iter(data.constraits)

next_definition : definition_model | None
next_constraint: constraint_model | None


try:
    next_definition = next(definition_iterator)
except StopIteration:
    next_definition = None

try:
    next_constraint = next(constraint_iterator)
except StopIteration:
    next_constraint = None

state = 0
last_exception : NameError | None = None
old_dependency_data:list[dependency_data_model] = []
try:
    with open("constraint_data.json", "r") as f:
        # Get memoized, hard mathematics
        old_dependency_data = [dependency_data_model.from_dict(d) for d in json.loads("\n".join(f.readlines()))]
except:
    pass


dependency_data:list[dependency_data_model] = []

dump_lines:list[str] = [f"Output results: {data.output}.svg"]

reflect_const = 1
expand_const = 2
contract_const = 0.5
shrink_const = 0.5

try:
    while True:
        match state:
            case 0:
                if next_definition == None:
                    state = 2
                    continue
                
                d = next_definition.definition
                if not next_definition.delayed:
                    try:
                        d = evaluate_expression(next_definition.definition)
                    except NameError as e:
                        last_exception = e
                        # missing variable, potentially defined by unevaluated constraint
                        state = 1
                        continue

                if next_definition.name != "":
                    variables[next_definition.name] = d
                    if dumping:
                        dump_lines.append(f"{next_definition.name} := {variables[next_definition.name]}" if next_definition.delayed else f"{next_definition.name} = {next_definition.definition}\n-> {variables[next_definition.name]}")
                elif dumping and not next_definition.delayed:
                    dump_lines.append(f"{next_definition.definition}\n-> {d}")
                try:
                    next_definition = next(definition_iterator)
                except StopIteration:
                    state = 2
                    next_definition = None
            case 1 | 2:
                if next_constraint == None:
                    if state == 1:
                        raise last_exception # type: ignore
                    # end of iteration
                    break
                (solution_found, best_solution) = load_previous_solution(next_constraint)
                if not solution_found:
                    # Nelder–Mead method
                    potential_solutions:list[list[float]] = []
                    potential_solutions_results:list[constraint_result] = []
                    for _ in range(100):
                        variable_count = len(next_constraint.variables)
                        current_amoeba:list[list[float]] = [[random.uniform(-5000, 5000) for i in range(variable_count)]]
                        for i in range(variable_count):
                            current_amoeba.append([current_amoeba[0][j] + (10 if j == i else 0) for j in range(variable_count)])
                        # initial evaluation
                        success = True
                        current_results:list[constraint_result] = []
                        for var_set in current_amoeba:
                            try:
                                current_results.append(evaluate_constraint_set(next_constraint, var_set))
                            except ArithmeticError, RecursionError, ValueError, ZeroDivisionError:
                                success = False
                                break
                        if not success:
                            continue
                        amoeba_steps = 0
                        while True:
                            #order
                            (current_results, current_amoeba) = sort_evaluations(current_results, current_amoeba)
                            # termination
                            if amoeba_steps >= 200:
                            # or (all([r[0] == 2 and r[1] == 0 for r in current_results]) and statistics.pvariance(data=[r[2] for r in current_results])) <= 0.01:
                                break
                            amoeba_steps += 1
                            # calcuate centroid
                            centroid = [statistics.mean([current_amoeba[i][j] for i in range(variable_count)]) for j in range(variable_count)]
                            # reflect
                            reflect = [centroid[i] + reflect_const * (centroid[i] - current_amoeba[-1][i]) for i in range(variable_count)]
                            reflect_result = evaluate_constraint_set(next_constraint, reflect)
                            if compare_constraint_sets(current_results[0], reflect_result) != -1 and compare_constraint_sets(reflect_result, current_results[-2]) == 1:
                                current_amoeba[-1] = reflect
                                current_results[-1] = reflect_result
                                continue
                            # expansion
                            if compare_constraint_sets(reflect_result, current_results[0]) == 1:
                                expansion = [centroid[i] + expand_const * (reflect[i] - centroid[i]) for i in range(variable_count)]
                                expansion_result = evaluate_constraint_set(next_constraint, expansion)
                                if compare_constraint_sets(expansion_result, reflect_result) == 1:
                                    current_amoeba[-1] = expansion
                                    current_results[-1] = expansion_result
                                else:
                                    current_amoeba[-1] = reflect
                                    current_results[-1] = reflect_result
                                continue
                            # contraction
                            if compare_constraint_sets(reflect_result, current_results[-1]) == 1:
                                contraction = [centroid[i] + contract_const * (reflect[i] - centroid[i]) for i in range(variable_count)]
                                contraction_result = evaluate_constraint_set(next_constraint, contraction)
                                if compare_constraint_sets(contraction_result, reflect_result) == 1:
                                    current_amoeba[-1] = contraction
                                    current_results[-1] = contraction_result
                                    continue
                            else:
                                contraction = [centroid[i] + contract_const * (current_amoeba[-1][i] - centroid[i]) for i in range(variable_count)]
                                contraction_result = evaluate_constraint_set(next_constraint, contraction)
                                if compare_constraint_sets(contraction_result, current_results[-1]) == 1:
                                    current_amoeba[-1] = contraction
                                    current_results[-1] = contraction_result
                                    continue
                            # shrink
                            for i in range(1, variable_count + 1):
                                current_amoeba[i] = [current_amoeba[0][j] + shrink_const * (current_amoeba[i][j] - current_amoeba[1][j]) for j in range(variable_count)]
                                current_results[i] = evaluate_constraint_set(next_constraint, current_amoeba[i])
                        potential_solutions.append(current_amoeba[0])
                        potential_solutions_results.append(current_results[0])
                    (potential_solutions_results, potential_solutions) = sort_evaluations(potential_solutions_results, potential_solutions)
                    best_solution = potential_solutions[0]
                if dumping:
                    for assertion in next_constraint.assertions:
                        dump_lines.append(f"{assertion} == 0")
                    if len(next_constraint.restrictions) > 0:
                        dump_lines.append("under the following constraints:")
                        for restriction in next_constraint.restrictions:
                            dump_lines.append(f"{restriction} <= 0")
                    dump_lines.append("->")
                
                for (varName, varValue) in zip(next_constraint.variables, best_solution):
                    if dumping:
                        dump_lines.append(f"{varName} = {varValue}")
                    variables[varName] = str(varValue)
                
                dependency_data.append(dependency_data_model(
                    constraint = next_constraint,
                    dependentVariables = get_dependent_expressions([*next_constraint.assertions, *next_constraint.restrictions], next_constraint.variables),
                    evaluations= best_solution
                ))

                try:
                    next_constraint = next(constraint_iterator)
                except StopIteration:
                    next_constraint = None
                state = 0
    with open("constraint_data.json", "w+") as f:
        # write the memos
        json.dump([asdict(d) for d in dependency_data], f, indent=2)
    if data.output != "":
        curve_output:list[curve_data] = []
        for curve in data.curves:
            param_count = 0
            arcSpecial = False
            match curve.type:
                case "A" | "a":
                    param_count = 7
                    arcSpecial = True
                case "C" | "c":
                    param_count = 6
                case "S" | "s" | "Q" | "q":
                    param_count = 4
                case "dot" | "L" | "l" | "M" | "m" | "T" | "t":
                    param_count = 2
                case "H" | "h" | "V" | "v":
                    param_count = 1
                case "Z" | "z":
                    param_count = 0
                case _:
                    raise Exception("Unknown path type " + curve.type)
            params:list[float | int] = []
            if param_count != 0:
                o = evaluate_expression(curve.params).split(" ")
                if len(o) < param_count:
                    raise Exception(f"Insuffient arguments in curve; got {len(o)}, require {param_count}")
                if len(o) > param_count:
                    raise Exception(f"Excessive arguments in curve; got {len(o)}, require {param_count}")
                for i in range(param_count):
                    (s, f) = convert_if_valid_float(o.pop(0))
                    if not s:
                        raise Exception("Parameters contains expression")
                    if arcSpecial and (i == 3 or i == 4):
                        params.append(int(f))
                    else:
                        params.append(f)
            curve_output.append(curve_data(curve.type, params, curve.debug))
        path_d:list[str] = []
        debug_data:list[str] = []
        current_x = 0
        current_y = 0
        start_x = 0
        start_y = 0
        i = 0
        while i < len(curve_output):
            curve = curve_output[i]
            if curve.command == "dot":
                [cx, cy] = curve_output.pop(i).params
                debug_data.append(f"<circle cx=\"{cx}\" cy=\"{cy}\" r=\"1\" fill=\"magenta\" />")
                continue

            # Convert to absolute
            match curve.command:
                case "a" | "l" | "m" | "t":
                    curve.params[-1] += current_y
                    curve.params[-2] += current_x
                case "c":
                    curve.params[0] += current_x
                    curve.params[1] += current_y
                    curve.params[2] += current_x
                    curve.params[3] += current_y
                    curve.params[4] += current_x
                    curve.params[5] += current_y
                case "h":
                    curve.params[0] += current_x
                case "s" | "q":
                    curve.params[0] += current_x
                    curve.params[1] += current_y
                    curve.params[2] += current_x
                    curve.params[3] += current_y
                case "v":
                    curve.params[0] += current_y
                case _:
                    pass
            curve.command = curve.command.upper()
            curve.carry_over()
            # create discrete
            match curve.discrete_command:
                case "H":
                    curve.discrete_command = "L"
                    curve.discrete_params.append(current_y)
                case "S":
                    c1X = current_x
                    c1Y = current_y
                    if curve_output[i - 1].discrete_command == "C":
                        c1X += current_x - curve_output[i - 1].discrete_params[2]
                        c1Y += current_y - curve_output[i - 1].discrete_params[3]
                    curve.discrete_command = "C"
                    curve.discrete_params.insert(0, c1Y)
                    curve.discrete_params.insert(0, c1X)
                case "T":
                    c1X = current_x
                    c1Y = current_y
                    if curve_output[i - 1].discrete_command == "Q":
                        c1X += current_x - curve_output[i - 1].discrete_params[0]
                        c1Y += current_y - curve_output[i - 1].discrete_params[1]
                    curve.discrete_command = "Q"
                    curve.discrete_params.insert(0, c1Y)
                    curve.discrete_params.insert(0, c1X)
                case "V":
                    curve.discrete_command = "L"
                    curve.discrete_params.insert(0, current_x)
                case "Z":
                    curve.discrete_command = "L"
                    curve.discrete_params = [start_x, start_y]
            if curve.debug:
                match curve.discrete_command:
                    case "A":
                        debug_data.append(f"<path d=\"M {current_x} {current_y} A {curve.discrete_params[0]} {curve.discrete_params[1]} {curve.discrete_params[2]} {curve.discrete_params[3]} {curve.discrete_params[4]} {curve.discrete_params[5]} {curve.discrete_params[6]}\" fill=\"none\" stroke=\"red\" />")
                        debug_data.append(f"<path d=\"M {current_x} {current_y} A {curve.discrete_params[0]} {curve.discrete_params[1]} {curve.discrete_params[2]} {1 - curve.discrete_params[3]} {1 - curve.discrete_params[4]} {curve.discrete_params[5]} {curve.discrete_params[6]}\" fill=\"none\" stroke=\"pink\" />")
                        debug_data.append(f"<circle cx=\"{current_x}\" cy=\"{current_y}\" r=\"1\" fill=\"lime\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[5]}\" cy=\"{curve.discrete_params[6]}\" r=\"1\" fill=\"red\" />")
                    case "C":
                        debug_data.append(f"<path d=\"M {current_x} {current_y} C {curve.discrete_params[0]} {curve.discrete_params[1]} {curve.discrete_params[2]} {curve.discrete_params[3]} {curve.discrete_params[4]} {curve.discrete_params[5]}\" fill=\"none\" stroke=\"red\" />")
                        debug_data.append(f"<line x1=\"{current_x}\" y1=\"{current_y}\" x2=\"{curve.discrete_params[0]}\" y2=\"{curve.discrete_params[1]}\" stroke=\"pink\" {" stroke-dasharray=\"0.5\" " if curve.command == "S" else ""}/>")
                        debug_data.append(f"<line x1=\"{curve.discrete_params[2]}\" y1=\"{curve.discrete_params[3]}\" x2=\"{curve.discrete_params[4]}\" y2=\"{curve.discrete_params[5]}\" stroke=\"pink\" />")
                        debug_data.append(f"<circle cx=\"{current_x}\" cy=\"{current_y}\" r=\"1\" fill=\"lime\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[0]}\" cy=\"{curve.discrete_params[1]}\" r=\"1\" fill=\"#b3c700\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[2]}\" cy=\"{curve.discrete_params[3]}\" r=\"1\" fill=\"#e58700\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[4]}\" cy=\"{curve.discrete_params[5]}\" r=\"1\" fill=\"red\" />")
                    case "L":
                        debug_data.append(f"<line x1=\"{current_x}\" y1=\"{current_y}\" x2=\"{curve.discrete_params[0]}\" y2=\"{curve.discrete_params[1]}\" stroke=\"red\" />")
                        debug_data.append(f"<circle cx=\"{current_x}\" cy=\"{current_y}\" r=\"1\" fill=\"lime\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[0]}\" cy=\"{curve.discrete_params[1]}\" r=\"1\" fill=\"red\" />")
                    case "M":
                        debug_data.append(f"<line x1=\"{current_x}\" y1=\"{current_y}\" x2=\"{curve.discrete_params[0]}\" y2=\"{curve.discrete_params[1]}\" stroke=\"red\" stroke-dasharray=\"0.4 0.6\" />")
                        debug_data.append(f"<circle cx=\"{current_x}\" cy=\"{current_y}\" r=\"1\" fill=\"lime\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[0]}\" cy=\"{curve.discrete_params[1]}\" r=\"1\" fill=\"red\" />")
                    case "Q":
                        debug_data.append(f"<path d=\"M {current_x} {current_y} Q {curve.discrete_params[0]} {curve.discrete_params[1]} {curve.discrete_params[2]} {curve.discrete_params[3]}\" fill=\"none\" stroke=\"red\" />")
                        debug_data.append(f"<path d=\"M {current_x} {current_y} L {curve.discrete_params[0]} {curve.discrete_params[1]} L {curve.discrete_params[2]} {curve.discrete_params[3]}\" fill=\"none\" stroke=\"pink\" {" stroke-dasharray=\"0.5\" " if curve.command == "T" else ""}/>")
                        debug_data.append(f"<circle cx=\"{current_x}\" cy=\"{current_y}\" r=\"1\" fill=\"lime\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[0]}\" cy=\"{curve.discrete_params[1]}\" r=\"1\" fill=\"#d0a800\" />")
                        debug_data.append(f"<circle cx=\"{curve.discrete_params[2]}\" cy=\"{curve.discrete_params[3]}\" r=\"1\" fill=\"red\" />")
            match curve.command:
                case "A" | "C" | "L" | "S" | "T" | "Q":
                    current_x = curve.params[-2]
                    current_y = curve.params[-1]
                case "H":
                    current_x = curve.params[0]
                case "M":
                    current_x = curve.params[0]
                    current_y = curve.params[1]
                    start_x = current_x
                    start_y = current_y
                case "V":
                    current_y = curve.params[0]
                case "v":
                    current_y += curve.params[0]
                case "Z" | "z":
                    current_x = start_x
                    current_y = start_y
            i += 1
        svg_output = f"<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"{data.minX} {data.minY} {data.width} {data.height}\" >\n"
        svg_output += "<path d=\"" + " ".join([str(c) for c in curve_output]) +"\" />\n"
        svg_output += "\n".join(debug_data) + "\n"
        svg_output += "</svg>"
        with open(data.output + ".svg", "w+") as f:
            f.write(svg_output)


    
except Exception as e:
    if dumping:
        dump_lines.append("")
        dump_lines.append("--------")
        dump_lines.append("The following error occurred:")
        dump_lines.append(str(e))
    raise
finally:
    if dumping:
        with open(data.dump + ".txt", "w+") as f:
            f.write("\n".join(dump_lines))