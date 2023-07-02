# SPR
Instead of doing random mutations on the erroneous programs, is it possible to evolve (or transform) programs in
more reasonable and determined ways? Answering this question brings opportunities in collaborating symbolic (and
even semantic) methods into mutations. SPR [F Long et al, 2015], standing for Staged Program Repair, is among
them. In this project, I am going to implement a proof-of-concept version of the SPR algorithm and apply it to repair
buggy Python code. Although SPR involves symbolic methods, the entire framework is quite dynamic and its
implementation recalls many of the key concepts and skills of AST
instrumentation, mutations, program states tracking, invariant mining, etc
