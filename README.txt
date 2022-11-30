S: v! - increment the accumulator
S: vN! - copy register N to the accumulator
S: vN? - copy the accumulator to register N
S: Nv. - swap the program counter (after incrementing) with register N
S: NvN'. - copy register N to N', then decrement N.
N: n | an | NNv
After tokenization, all tokens that are not Buffalo, buffalo, ! ? or . are stripped.
Invalid sentences (including empty sentences) are rejected.
At the start of a sentence, 'a', 'n', 'v' are all capitalized; elsewhere only 'a' is.
For example, 'nnvv.' and 'anvn.' are both written as "Bbbb.", but 'nvan.' is written "BbBb.".
"bbbbb" names two distinct registers ('nnnvv' and 'nnvnv')!
pc, acc and all registers are initially zero.
I/O is mapped to registers 'n' for numeric and 'an' for Unicode.
Loop: read the sentence at pc, then increment pc.
Order the K valid interpretations as they are produced by the grammar L-R; execute the instruction at min(acc, K - 1).
The program halts when it reaches the end.
