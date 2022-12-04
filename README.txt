Buffalo! is a register machine language based on a linguistics joke.

Although it is Turing-complete, it is designed to be extremely annoying to write, not to mention almost impossible to read, notwithstanding that every Buffalo! program is a valid text in English (the linguistics joke).
Even *parsing* a Buffalo! program takes exponential time in sentence length (the parser cheats by spotting patterns used by the author and the transpiler).
The principal annoyance is that (like English) parsing a Buffalo! program is *ambiguous*, but that ambiguity is used for *conditional branching* (dependent on the value of the accumulator register) so must be employed in any nontrivial program while being avoided anywhere linear control flow is required.
Also, jump targets are numeric (the program counter) but since the only increasing numeric primitive is to increment the accumulator, jumping forward is quite tricky.
Finally, jumping destroys the jump target (it swaps the jump target register with the program counter); this is useful for obtaining return locations (or even just to get large numbers without having to repeatedly increment the accumulator) but means that if you want to jump to the same target more than once you need to copy the location into a scratch register.

Proof of Turing completeness is by transpilation from a high(er)-level language.
This exhibits extreme blowup; for example, the 42-line (910 byte) "99 bottles of beer" program transpiles to 18805 lines (229 KB) of Buffalo!.

Syntax and semantics
====================
A Buffalo! program is a list of sentences.
Each sentence is in the imperative (punctuation "!") or indicative (".").
Imperative sentences have implied second person pronoun subject, and can be intransitive ("<verb>!") or transitive ("<verb> <object>!"), where the object is a noun phrase.
Likewise, indicative sentences can be intransitive ("<subject> <verb>.") or transitive ("<subject> <verb> <object>.").

Of course, the only verb allowed is "buffalo", meaning "to intimidate".
And the noun phrases are formed from the noun "buffalo" (viz. bovines), the adjective "Buffalo" (e.g. "Buffalo(1) buffalo(2)", bovines (2) from the town in New York state (1)), and the verb "buffalo" in a reduced object passive relative clause (e.g. "buffalo(1) buffalo(2) buffalo(3)", bovines(3) which are intimidated by(2) bovines(1)).
Since the reduced object passive relative clause can take any noun phrase in its object and subject positions, this is a recursive construction, allowing sentences of any length.
The capitalization of the adjective allows (incomplete) disambiguation; for example, "Buffalo buffalo Buffalo buffalo." can only be read as an intransitive indicative, with object "Buffalo buffalo", but "Buffalo buffalo buffalo buffalo." could be either transitive (with subject "Buffalo buffalo"), or intransitive (with subject "buffalo buffalo buffalo", the first word capitalized because of the rules of English orthography despite not being the adjective).
For another example, "Buffalo buffalo buffalo buffalo buffalo buffalo!" must be a transitive indicative, but there are two possible constructions for the noun phrase, either "buffalo (buffalo buffalo buffalo) buffalo" or "(buffalo buffalo buffalo) buffalo buffalo"; these are considered distinct sentences.

Schematically:

S: v! - increment the accumulator
S: vN! - swap the accumulator with register N
S: Nv. - swap the program counter (after incrementing) with register N
S: NvN'. - copy register N to N', then decrement N.
N: n | an | NNv
After tokenization, all tokens that are not Buffalo, buffalo, ! or . are stripped.
Invalid sentences are rejected; empty sentences are ignored.
At the start of a sentence, 'a', 'n', 'v' are all capitalized; elsewhere only 'a' is.
For example, 'nnvv.' and 'anvn.' are both written as "Bbbb.", but 'nvan.' is written "BbBb.".
"bbbbb" names two distinct registers ('nnnvv' and 'nnvnv')!
pc, acc and all registers are initially zero.
I/O is mapped to register 'n': for input, "nvN." reads a Unicode codepoint into register N; for output, "Nvn." writes register N as a Unicode codepoint (make sure to set acc appropriately first).
The instructions 'vn!' and 'nv.' do something weird.
Execution proceeds by repeatedly reading the sentence at pc, then incrementing pc.
To evaluate a sentence, order the K valid interpretations as they are produced by the grammar L-R; execute the instruction at min(acc, K - 1).
The program halts when it reaches the end.
