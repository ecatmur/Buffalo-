import argparse
import collections
import functools
import os.path
import re
import sys

args = argparse.Namespace()

def case(s):
    return 'B' + ''.join({'a':'B','n':'b','v':'b','B':'B','b':'b'}[c] for c in s[1:])

def decompile(s):
    return ' '.join(c + 'uffalo' for c in case(s[:-1])) + s[-1]

def m2(t, n):
    if len(t) > n:
        return
    elif len(t) == n:
        yield ''.join({'N':'n'}.get(c, c) for c in t)
    else:
        i = t.find('N')
        if i != -1:
            yield from m2(t[:i] + 'n' + t[i+1:], n)
            yield from m2(t[:i] + 'an' + t[i+1:], n)
            yield from m2(t[:i] + 'NNv' + t[i+1:], n)

@functools.cache
def match(t, s):
    return [y for y in m2(t, len(s)) if case(y) == s]

@functools.cache
def compile_(s):
    x = case(s[:-1])
    l = ([m + s[-1] for m in match('v', x)] if s[-1] == '!' and len(s) == 2 else
        [m + s[-1] for m in match('vN', x)] if s[-1] in '!?' else
        [m + '^' for m in match('Nv', x)] + [m + '-' for m in match('NvN', x)] if s[-1] == '.' else
        None)
    return l

def sentences(f):
    lines = f.readlines()
    for l in lines:
        i = l.find('//')
        if i != -1:
            l = l[:i]
        l = l.strip()
        if not l:
            continue
        yield from l.split()

def parse(f):
    s = ''
    for w in f.read().split():
        if w in {'Buffalo', 'buffalo'}:
            s += w[0]
        elif w[-1] in {'!', '?', '.'} and w[:-1] in {'Buffalo', 'buffalo'}:
            s += w[0] + w[-1]
            yield s
            s = ''

def unpack2(p):
    j = 0
    for i, c in enumerate(p[:-1]):
        j += {'n':1,'v':-1,'a':0}[c]
        if j == 0:
            break
    return p[:i], p[i+1:-1]

def describe(p):
    if p == 'v!':
        return "++a"
    elif p[-1] == '!':
        return "a<-" + p[1:-1]
    elif p[-1] == '?':
        return p[1:-1] + "<-a"
    elif p[-1] == '^':
        return "p<->" + p[:-2]
    else:
        p1, p2 = unpack2(p)
        return f"{p2}<-{p1}--"

def transpile(path):
    basename, ext = os.path.splitext(path)
    if ext != '.mmn':
        raise Exception(path)
    def next_register():
        r = 'ananv'
        while True:
            yield r
            r = f'an{r}v'
    next_register = next_register().__next__
    running = next_register()
    registers = {}
    def get_register(reg):
        if not isinstance(reg, str):
            raise Exception(reg)
        if reg not in registers:
            registers[reg] = next_register()
        return registers[reg]
    subroutines = collections.defaultdict(list)
    stack = [[0, subroutines['']]]
    with open(path) as f:
        for line in f:
            m = re.match(r'( *)(\w*)(?: ([^\n]*))?\n?', line)
            indent, op, args = len(m.group(1)), m.group(2), (m.group(3) or '').split(' ')
            while indent < stack[-1][0]:
                stack.pop()
            ops = stack[-1][1]
            if not ops:
                stack[-1][0] = indent
            if op == 'if':
                arg, = args
                reg = get_register(arg)
                if_reg = next_register()
                ops.append([op, reg, if_reg])
                stack.append([0, subroutines[if_reg]])
            elif op == 'else':
                else_reg = next_register()
                ops[-1].append(else_reg)
                stack.append([0, subroutines[else_reg]])
            elif op == 'def':
                arg, = args
                reg = get_register(arg)
                stack.append([0, subroutines[reg]])
            elif op == 'print':
                args = [' '.join(args).encode('latin-1', 'backslashreplace').decode('unicode-escape')]
                ops.append([op, *args])
            else:
                args = [int(x) if re.match('[0-9]+', x) else get_register(x) for x in args]
                ops.append([op, *args])
    def goto(r):
        return f"vnnv! v{r}! vnanv? vnnv! nanvv.".split()
    def set_acc(n):
        return ['vnnv!'] + ['v!'] * n
    for name, ops in subroutines.items():
        insns = []
        if name:
            return_reg = next_register()
            insns.extend(f"""
vnnv! vnanv! v{return_reg}? vnannvv? nannvvv. nanvvnanv. nanvvnanv. nanvvnanv. nanvvnanv. nanvvnanv. vnanv! v{name}?
vananv! vnanv? vnnv! vnanvnv? v! v! v! v! v! vnannvv? vnanv! nannvvv.
vannv! vnanv? nanvv. v! v! v! v! v! v! v! v!
            """.strip().split())
        for op, *args in ops:
            if op == 'input':
                reg = get_register(*args)
                insns.extend(['van!', f'v{reg}?'])
            elif op == 'output':
                arg, = args
                if isinstance(arg, int):
                    insns.extend(set_acc(arg) + ['van?'])
                else:
                    reg = get_register(*args)
                    insns.extend([f'v{reg}!', 'van?'])
            elif op == 'if':
                if len(args) == 2:
                    p, q = args
                    insns.extend(f"""
    vnnv! vnanvnv? v! v! v! v! v! vnannvv? v{p}! nannvvv.
    v! v! nannvvv. v! v! v! v! v! v! v! v!
    v{q}! vnanv? nanvv.
                    """.strip().split())
                else:
                    p, q, r = args
                    insns.extend(f"""
    vnnv! vnanvnv? v! v! v! v! v! vnannvv? v{p}! nannvvv.
    v{r}! vnanv? nanvv. vnnv! v! v! v! v! v! vnannvv? nannvvv.
    v{q}! vnanv? nanvv. v! v! v! v! v! v! v! v!
                    """.strip().split())
            elif op == 'label':
                r, = args
                insns.extend(f"vnnv! vnannvv? nannvvv. nanvvnanv. nanvvnanv. nanvvnanv. vnanv! v{r}?".split())
            elif op == 'goto':
                insns.extend(goto(*args))
            else:
                raise NotImplementedError(op, args)
        if name:
            insns.extend(goto(return_reg))
        subroutines[name] = insns

    program = """
vnnv! vnannvv! vnanv? vnnv! nannvvv.
v! vnanvnv! v! v! v! v! v! v! v! v! v! v! v! vnanvnv? vnanv? v! nanvnvv.
    """.strip().split()
    L = max(len(insns) - 27 for name, insns in subroutines.items() if name)
    program.extend(["vnanv!"] + ["v!"] * L + "vnanv? v! nanvv. v! vnanvnv! vannv?".split())
    program.extend("vnnv! vananv?".split())
    for name, insns in subroutines.items():
        if name:
            program.extend(insns)
            program.extend(["v!"] * (L - (len(insns) - 27)))
    program.extend("vnnv! v! vananv?".split())
    program.extend(subroutines[""])
    with open(basename + '.Buffalo!', 'w') as f:
        for s in program:
            print(decompile(s), file=f)

def run(path):
    basename, ext = os.path.splitext(path)
    if ext != '.Buffalo!':
        raise Exception(path)
    program = [compile_(s) for s in parse(open(path))]
    if args.compile:
        for i, pp in enumerate(program):
            print(f"[{i}] " + ', '.join(describe(p) for p in pp))
        return
    evaluate(program)

def evaluate(program):
    pc = 0
    acc = 0
    reg = {}
    def load(r):
        if r == 'n':
            return ord(sys.stdin.read(1))
        elif r == 'an':
            return int(input("Buffalo Buffalo buffalo? "))
        else:
            return reg.get(r, 0)
    def store(r, x):
        if r == 'n':
            sys.stdout.write(chr(x))
        elif r == 'an':
            print(f"Buffalo Buffalo buffalo! {x}")
        else:
            reg[r] = x
    while True:
        if pc >= len(program):
            break
        pp = program[pc]
        if args.trace:
            print(pc, pp, acc, reg)
        pc += 1
        p = pp[min(acc, len(pp) - 1)]
        if p == 'v!':
            acc += 1
        elif p[-1] == '!':
            acc = load(p[1:-1])
        elif p[-1] == '?':
            store(p[1:-1], acc)
        elif p[-1] == '^':
            tmp, pc = pc, load(p[:-2])
            if args.trace:
                print(f"jump to {p[:-2]}: {pc}<->{tmp}")
            store(p[:-2], tmp)
        else:
            p1, p2 = unpack2(p)
            k = load(p1)
            store(p2, k)
            store(p1, max(k-1, 0))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script")
    parser.add_argument("--trace", action='store_true')
    parser.add_argument("--compile", action='store_true')
    parser.add_argument("--transpile", action='store_true')
    parser.add_argument("--describe", type=str)
    parser.add_argument("--decompile", type=str)
    parser.add_argument("--execute", type=str)
    parser.parse_args(namespace=args)
    if args.describe:
        for s in args.describe.split():
            print(', '.join(describe(p) for p in compile_(s)))
    elif args.decompile:
        for s in args.decompile.split():
            print(decompile(s))
    elif args.execute:
        program = [compile_(s) for s in args.execute.split()]
        evaluate(program)
    elif args.transpile:
        transpile(args.script)
    else:
        run(args.script)

if __name__ == "__main__":
    main()
