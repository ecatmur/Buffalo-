import sys

def case(s):
    return 'B' + ''.join({'a':'B','n':'b','v':'b','B':'B','b':'b'}[c] for c in s[1:])

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

def match(t, s):
    return [y for y in m2(t, len(s)) if case(y) == s]

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

def main(argv):
    #for s in sentences(open(argv[1])):
    #    print(' '.join(c + 'uffalo' for c in case(s[:-1])) + s[-1])
    program = [compile_(s) for s in parse(open(argv[1]))]
    pc = 0
    acc = 0
    reg = {}
    def load(r):
        if r == 'n':
            return int(input("Buffalo? "))
        else:
            return reg.get(r, 0)
    def store(r, x):
        if r == 'n':
            print(f"Buffalo! {x}")
        else:
            reg[r] = x
    while True:
        if pc >= len(program):
            break
        pp = program[pc]
        # print(pc, pp, acc, reg)
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
            # print(f"jump to {p[:-2]}")
            store(p[:-2], tmp)
        else:
            j = 0
            for i, c in enumerate(p[:-1]):
                j += {'n':1,'v':-1,'a':0}[c]
                if j == 0:
                    break
            k = load(p[:i-1])
            store(p[i+1:-1], k)
            store(p[:i-1], max(k-1, 0))

if __name__ == "__main__":
    main(sys.argv)
