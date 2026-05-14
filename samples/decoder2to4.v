// -----------------------------------------------------------------------------
// decoder2to4.v -- 2-to-4 decoder with enable (structural)
//
// Exercises: fanout analysis (each input drives multiple outputs),
//            primary-input -> primary-output dependency chains.
// License: public-domain textbook design.
// -----------------------------------------------------------------------------

module decoder2to4 (
    input  wire       en,
    input  wire [1:0] sel,
    output wire [3:0] y
);
    wire ns0, ns1;

    not (ns0, sel[0]);
    not (ns1, sel[1]);

    and (y[0], en, ns1, ns0);
    and (y[1], en, ns1, sel[0]);
    and (y[2], en, sel[1], ns0);
    and (y[3], en, sel[1], sel[0]);
endmodule
