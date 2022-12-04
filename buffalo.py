import argparse
import collections
import functools
import os.path
import re
import sys
import textwrap

args = argparse.Namespace()

def case(s, start):
    return 'B' + case(s[1:], False) if start else ''.join({'a':'B','n':'b','v':'b','B':'B','b':'b'}[c] for c in s)

def decompile(subj, op, obj):
    if op == '+':
        assert subj is None and obj is None
        return "v!"
    elif op == '@':
        assert subj is None
        return f"v{obj}!"
    elif op == '^':
        assert obj is None
        return f"{subj}v."
    elif op == '-':
        return f"{subj}v{obj}."

def unparse(s):
    assert any(s == decompile(subj, op, obj) for subj, op, obj in compile_(s)), s
    return ' '.join(c + 'uffalo' for c in case(s[:-1], True)) + s[-1]

@functools.cache
def match(t, s, start):
    n = len(s)
    if len(t) > n:
        return []
    elif len(t) == n:
        y = ''.join({'N':'n'}.get(c, c) for c in t)
        return [y] if case(y, start) == s else []
    if t == 'N' and n % 3 == 2 and not start:
        m = (n + 1) // 3
        if s == 'Bb' * m + 'b' * (m - 1):
            return ['an' * m + 'v' * (m - 1)]
    i = t.find('N')
    if i == -1 or case(t[:i], start) != case(s[:i], start):
        return []
    r = []
    r += match(t[:i] + 'n' + t[i+1:], s, start)
    r += match(t[:i] + 'an' + t[i+1:], s, start)
    r += match(t[:i] + 'NNv' + t[i+1:], s, start)
    return r

def compile_(s):
    x = case(s[:-1], True)
    if s[-1] == '!':
        return [(None, '+', None)] if x == 'B' else [(None, '@', m) for m in match('N', x[1:], False)]
    elif s[-1] == '.':
        return [(m, '^', None) for m in match('N', x[:-1], True)] + [(m, '-', n)
                for i in range(len(x) - 1) for m in match('N', x[:i], True) for n in match('N', x[i+1:], False)
                if x[i] == 'b']

def parse(f):
    s = ''
    for w in f.read().split():
        if w in {'Buffalo', 'buffalo'}:
            s += w[0]
        elif w[-1] in {'!', '.'} and w[:-1] in {'Buffalo', 'buffalo'}:
            s += w[0] + w[-1]
            yield s
            s = ''

def describe(subj, op, obj):
    if op == '+':
        assert subj is None and obj is None
        return "++a"
    elif op == '@':
        assert subj is None
        return "a<->" + obj
    elif op == '^':
        assert obj is None
        return "p<->" + subj
    elif op == '-':
        return f"{obj}<-{subj}--"

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
    uses_if = False
    with open(path) as f:
        for line in f:
            m = re.match(r'( *)(\w*)(?: ([^\n]*))?\n?', line)
            indent, op, argv = len(m.group(1)), m.group(2), (m.group(3) or '').split(' ')
            while indent < stack[-1][0]:
                stack.pop()
            ops = stack[-1][1]
            if not ops:
                stack[-1][0] = indent
            if op == 'if':
                uses_if = True
                arg, = argv
                reg = get_register(arg)
                if_reg = next_register()
                ops.append([op, reg, if_reg])
                stack.append([indent + 1, subroutines[if_reg]])
            elif op == 'else':
                else_reg = next_register()
                ops[-1].append(else_reg)
                stack.append([0, subroutines[else_reg]])
            elif op == 'def':
                arg, = argv
                reg = get_register(arg)
                stack.append([0, subroutines[reg]])
            elif op == 'print':
                argv = [' '.join(argv).encode('latin-1', 'backslashreplace').decode('unicode-escape')]
                ops.append([op, *argv])
            else:
                argv = [int(x) if re.match('[0-9]+', x) else get_register(x) for x in argv]
                ops.append([op, *argv])
    def goto(r):
        return f"v{r}! v! vnanv! nanvvan. anvan. van! v{r}! nanvv.".split()
    def inc_acc(n):
        return ['v!'] * n
    def set_acc(n):
        return 'nnvvan. van!'.split() + inc_acc(n)
    def dec_acc(n):
        return ['van!'] + ['anvan.'] * n + ['van!']
    def label(r, n=0):
        return "nnvvan. van! vnannvv! nnvvan. van! nannvvv.".split() + ["nanvvnanv."] * (6 + n) + f"vnanv! v{r}!".split()
    def pad2(i, n):
        return i + ["v!"] * (n - len(i))
    def pad3(m, i, n):
        return ["v!"] * (m - len(i)) + i + ["v!"] * (n - m)
    N = 11
    K = 24
    J = 51
    def if1(p):
        return ("nnvvan. van! vnanvnv! nnvvan. van!".split() + ["v!"] * N + f"""vnannvv!
                v{p}! v! vnanv! nanvvan. vnanv! anvan. v{p}! van!
                nannvvv.""".strip().split())
        # [¬p branch padded to K with v!]
        # [p branch]
    def if2(p, q):
        return if1(p) + pad3(len(goto(q)), ["nannvvv."], K) + goto(q)
    def if3(p, q, r):
        else_block = goto(r) + set_acc(N) + "vnannvv! v! nannvvv.".split()
        assert len(else_block) == K, (len(else_block), K)
        return if1(p) + else_block + pad2(goto(q), K)
    def def_(r, s):
        save_return = f"vnanv! v{s}!".split()
        return save_return + label(r, len(save_return)) + if1("ananv") + pad2(goto("annv"), K)

    for name, ops in subroutines.items():
        insns = []
        if name:
            return_reg = next_register()
            insns.extend(def_(name, return_reg))
        for op, *argv in ops:
            if op == 'if':
                if len(argv) == 2:
                    insns.extend(if2(*argv))
                else:
                    insns.extend(if3(*argv))
            elif op == 'label':
                insns.extend(label(*argv))
            elif op == 'goto':
                insns.extend(goto(*argv))
            elif op == 'set':
                q, r = argv
                if isinstance(r, int):
                    insns.extend(set_acc(r) + [f"v{q}!"])
                else:
                    insns.extend(f"v{r}! v! van! anvnanv. nanvvnanv. van! v{r}! vnanv! v{q}!".split())
            elif op == 'dec':
                arg, n = argv + ([1] if len(argv) == 1 else [])
                insns.extend(f"v{arg}! van!".split() + ["anvan."] * n + f"van! v{arg}!".split())
            elif op == 'inc':
                arg, n = argv + ([1] if len(argv) == 1 else [])
                insns.extend([f"v{arg}!"] + inc_acc(n) + [f"v{arg}!"])
            elif op == 'read':
                arg, = argv
                insns.extend(f"nvan. van! v{arg}!".split())
            elif op == 'write':
                arg, = argv
                insns.extend(f"v{arg}! v! van! anvnanv. nanvvnanv. van! v{arg}! nanvvn.".split())
            elif op == 'print':
                s, = argv
                insns.extend(set_acc(0) + ['van!'])
                current = 0
                for c in s:
                    if ord(c) >= current:
                        if insns[-1] == 'van!':
                            insns.pop()
                        else:
                            insns.append('van!')
                        insns.extend(inc_acc(ord(c) - current) + ['van!'])
                    elif ord(c) >= current / 2:
                        insns.extend(['anvan.'] * (current - ord(c)))
                    else:
                        insns.extend(set_acc(ord(c)) + ['van!'])
                    insns.extend(inc_acc(1) + ['anvn.'])
                    current = max(ord(c) - 1, 0)
            else:
                raise NotImplementedError(op, argv)
        if name:
            insns.extend(goto(return_reg))
        subroutines[name] = insns

    program = []
    if uses_if or len(subroutines) > 1:
        # [0] J+0: jump to nannvv, storing address in nanv (N = 11)
        program.extend("nnvvan. van! vnannvv! vnanv! nnvvan. van! nanvvnannvv. vnanv! v! vnanv! nannvvv.".split())
        assert len(program) == N

        # [N] J+K: jump to nanvnv + K, storing address in nanv
        program.extend("v! vnanvnv!".split() + ["v!"] * K + """vnanv! nnvvan. van!
v! nanvvnanvnv. vnanv! v! van! anvnanv. van! v! v! v! v! v! v! nanvnvv.
        """.strip().split())

    if len(subroutines) > 1:
        # [annv] J+L: jump to nanv + L (L >= 3)
        L = max(3, max((len(insns) - J for name, insns in subroutines.items() if name), default=0))
        program.extend(["vnanv!"] + ["v!"] * L + "vnanv! v! nanvv.".split() + ["v!"] * L + "vnanvnv! vannv!".split())

        if args.trace:
            print(L, J, file=sys.stderr)
        for name, insns in subroutines.items():
            if name:
                if args.trace:
                    print(name, len(program), len(insns), (L - (len(insns) - J)), file=sys.stderr)
                program.extend(insns)
                program.extend(["v!"] * (L - (len(insns) - J)))
        # SET RUNNING FLAG
        if args.trace:
            print(len(program), file=sys.stderr)
        program.extend("v! vananv!".split())

    if args.trace:
        print(len(program), file=sys.stderr)
    program.extend(subroutines[""])
    if args.trace:
        print(len(program))
    with open(basename + '.Buffalo!', 'w') as f:
        if args.wrap:
            line = []
            for s in program:
                for w in unparse(s).split():
                    if len(' '.join(line + [w])) <= args.wrap:
                        line.append(w)
                        continue
                    ww, line = line, [w]
                    x = args.wrap - len(' '.join(ww))
                    q, r = divmod(x, len(ww) - 1)
                    for i, w in enumerate(ww):
                        f.write(' ' * (0 if i == 0 else q + 2 if i <= (r + 1) else q + 1) + w)
                    f.write('\n')
            f.write(' '.join(line) + '\n')
        else:
            for s in program:
                print(unparse(s), file=f)

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
    pc = acc = 0
    reg = {}
    def get(r):
        return ord(sys.stdin.read(1) or '\0') if r == 'n' else reg.get(r, 0)
    def put(r, n):
        if r == 'n':
            sys.stdout.write(chr(n))
        else:
            reg[r] = n
    while True:
        if pc >= len(program):
            break
        pp = program[pc]
        if args.trace:
            print(pc, pp, acc, reg, file=sys.stderr)
        pc += 1
        subj, op, obj = pp[min(acc, len(pp) - 1)]
        if op == '+':
            acc += 1
        elif op == '@':
            tmp, acc = acc, get(obj)
            put(obj, tmp)
        elif op == '^':
            tmp, pc = pc, get(subj)
            if args.trace:
                print(f"jump to {subj}: {pc}<->{tmp}", file=sys.stderr)
            put(subj, tmp)
        elif op == '-':
            put(obj, get(subj))
            if subj != 'n':  # should peek and discard, nvm
                put(subj, max(0, get(subj) - 1))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script")
    parser.add_argument("--trace", action='store_true')
    parser.add_argument("--compile", action='store_true')
    parser.add_argument("--transpile", action='store_true')
    parser.add_argument("--wrap", type=int, default=120)
    parser.add_argument("--describe", type=str)
    parser.add_argument("--unparse", type=str)
    parser.add_argument("--execute", type=str)
    parser.parse_args(namespace=args)
    if args.describe:
        for s in args.describe.split():
            print(', '.join(describe(*p) for p in compile_(s)))
    elif args.unparse:
        for s in args.unparse.split():
            print(unparse(s))
    elif args.execute:
        program = [compile_(s) for s in args.execute.split()]
        evaluate(program)
    elif args.transpile:
        transpile(args.script)
    else:
        run(args.script)

if __name__ == "__main__":
    main()
