// Simple Counter Module for Testing DAG Visualization

module test_counter (
    input wire clk,
    input wire rst_n,
    input wire enable,
    input wire [7:0] load_value,
    output reg [7:0] count,
    output wire overflow,
    output wire underflow
);

// Internal signals
reg [7:0] next_count;
wire count_up;
wire count_down;

// Combinational logic
assign count_up = enable & ~rst_n;
assign count_down = ~enable & ~rst_n;
assign overflow = (count == 8'hFF);
assign underflow = (count == 8'h00);

// Next count logic (combinational)
always @(*) begin
    if (count_up)
        next_count = count + 1;
    else if (count_down)
        next_count = count - 1;
    else
        next_count = load_value;
end

// Sequential logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= 8'h00;
    else
        count <= next_count;
end

endmodule
