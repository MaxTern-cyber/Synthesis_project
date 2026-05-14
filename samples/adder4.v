// -----------------------------------------------------------------------------
// adder4.v -- 4-bit ripple-carry adder (structural)
//
// Exercises: critical path, cone-of-influence, combinational depth.
// License: public-domain textbook design (no third-party IP).
// -----------------------------------------------------------------------------

module full_adder (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire sum,
    output wire cout
);
    wire ab, acin, bcin;
    xor (sum,  a, b, cin);
    and (ab,   a, b);
    and (acin, a, cin);
    and (bcin, b, cin);
    or  (cout, ab, acin, bcin);
endmodule


module adder4 (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire       cin,
    output wire [3:0] sum,
    output wire       cout
);
    wire c1, c2, c3;

    full_adder fa0 (.a(a[0]), .b(b[0]), .cin(cin), .sum(sum[0]), .cout(c1));
    full_adder fa1 (.a(a[1]), .b(b[1]), .cin(c1),  .sum(sum[1]), .cout(c2));
    full_adder fa2 (.a(a[2]), .b(b[2]), .cin(c2),  .sum(sum[2]), .cout(c3));
    full_adder fa3 (.a(a[3]), .b(b[3]), .cin(c3),  .sum(sum[3]), .cout(cout));
endmodule
