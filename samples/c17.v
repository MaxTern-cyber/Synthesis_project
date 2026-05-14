// -----------------------------------------------------------------------------
// c17.v -- ISCAS-85 benchmark: c17
//
// The smallest of the ISCAS-85 combinational benchmark suite -- 5 primary
// inputs, 2 primary outputs, 6 NAND gates. Classic verification / ATPG
// micro-benchmark used in dozens of academic EDA papers.
//
// Source: ISCAS-85 benchmark suite (Brglez & Fujiwara, ISCAS 1985).
//         The c17 topology is public-domain prior art.
//
// Connectivity (canonical):
//   N10 = NAND(N1,  N3)
//   N11 = NAND(N3,  N6)
//   N16 = NAND(N2,  N11)
//   N19 = NAND(N11, N7)
//   N22 = NAND(N10, N16)   -- primary output
//   N23 = NAND(N16, N19)   -- primary output
//
// License: public-domain textbook circuit, re-written for this project.
// -----------------------------------------------------------------------------

module c17 (
    input  wire N1,
    input  wire N2,
    input  wire N3,
    input  wire N6,
    input  wire N7,
    output wire N22,
    output wire N23
);
    wire N10, N11, N16, N19;

    nand (N10, N1,  N3);
    nand (N11, N3,  N6);
    nand (N16, N2,  N11);
    nand (N19, N11, N7);
    nand (N22, N10, N16);
    nand (N23, N16, N19);
endmodule
