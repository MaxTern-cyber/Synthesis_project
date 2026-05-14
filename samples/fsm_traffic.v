// -----------------------------------------------------------------------------
// fsm_traffic.v -- 4-state traffic-light controller FSM
//
// Exercises: FSM detection, sequential analysis, register graph patterns,
//            clock-domain propagation, reset-tree visualization.
// License: public-domain textbook design.
// -----------------------------------------------------------------------------

module fsm_traffic (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       sensor,    // car-present sensor on side road
    output reg  [1:0] ns_light,  // 00=R, 01=Y, 10=G
    output reg  [1:0] ew_light
);
    // State encoding
    localparam S_NS_GREEN  = 2'b00;
    localparam S_NS_YELLOW = 2'b01;
    localparam S_EW_GREEN  = 2'b10;
    localparam S_EW_YELLOW = 2'b11;

    reg [1:0] state, next_state;

    // State register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) state <= S_NS_GREEN;
        else        state <= next_state;
    end

    // Next-state logic
    always @(*) begin
        case (state)
            S_NS_GREEN:  next_state = sensor ? S_NS_YELLOW : S_NS_GREEN;
            S_NS_YELLOW: next_state = S_EW_GREEN;
            S_EW_GREEN:  next_state = sensor ? S_EW_GREEN  : S_EW_YELLOW;
            S_EW_YELLOW: next_state = S_NS_GREEN;
            default:     next_state = S_NS_GREEN;
        endcase
    end

    // Output logic (Moore)
    always @(*) begin
        case (state)
            S_NS_GREEN:  begin ns_light = 2'b10; ew_light = 2'b00; end
            S_NS_YELLOW: begin ns_light = 2'b01; ew_light = 2'b00; end
            S_EW_GREEN:  begin ns_light = 2'b00; ew_light = 2'b10; end
            S_EW_YELLOW: begin ns_light = 2'b00; ew_light = 2'b01; end
            default:     begin ns_light = 2'b00; ew_light = 2'b00; end
        endcase
    end
endmodule
