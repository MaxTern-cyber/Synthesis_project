// -----------------------------------------------------------------------------
// mux4to1.v -- 4-to-1 multiplexer (structural)
//
// Exercises: cone-of-influence, fanin tracing, basic combinational logic.
// License: public-domain textbook design.
// -----------------------------------------------------------------------------

module mux4to1 (
    input  wire [3:0] d,
    input  wire [1:0] sel,
    output wire       y
);
    wire ns0, ns1;
    wire t0, t1, t2, t3;

    not (ns0, sel[0]);
    not (ns1, sel[1]);

    and (t0, d[0], ns1, ns0);
    and (t1, d[1], ns1, sel[0]);
    and (t2, d[2], sel[1], ns0);
    and (t3, d[3], sel[1], sel[0]);

    or  (y, t0, t1, t2, t3);
endmodule
