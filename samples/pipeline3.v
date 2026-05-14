// -----------------------------------------------------------------------------
// pipeline3.v -- 3-stage register pipeline with combinational stages
//
// Exercises: pipeline detection, register-chain depth, critical path across
//            multiple sequential stages, longest-path-on-DAG.
// License: public-domain textbook design.
// -----------------------------------------------------------------------------

module pipeline3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  a,
    input  wire [7:0]  b,
    output reg  [8:0]  result
);
    reg  [7:0] a_s1, b_s1;
    reg  [8:0] sum_s2;
    wire [8:0] sum_w;

    // Stage 1: register inputs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_s1 <= 8'd0;
            b_s1 <= 8'd0;
        end else begin
            a_s1 <= a;
            b_s1 <= b;
        end
    end

    // Stage 2: combinational add, register result
    assign sum_w = a_s1 + b_s1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) sum_s2 <= 9'd0;
        else        sum_s2 <= sum_w;
    end

    // Stage 3: register output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) result <= 9'd0;
        else        result <= sum_s2;
    end
endmodule
