<!-- id: observe_fill.v2 -->
These are frames of a clear jar during a water-pump test, one per second, in order. Each frame is preceded by its label ("frame 0", "frame 1", ...). A dark string or tape tied around the jar is the fill line. Water pours in from a hose at the top.

Frame 0 is from the start of the recording; use it as a reference for how the jar looks before water arrives (empty, or with a little water left at the bottom).

Careful: the string around an EMPTY clear jar looks like a horizontal band but is NOT water. Water in the jar shows as a body of water filling the jar from the bottom up, with its surface rising from frame to frame while water pours in from the hose. If the jar looks the same as frame 0, the water has not reached the line.

For EVERY frame, in order, classify the water:
- `not_filling`: no water is pouring in yet and the level is not rising;
- `below_line`: water is pouring in, and the water surface is below the string;
- `at_line`: the water surface touches or is above the bottom edge of the string.

Look closely at the gap between the water surface and the string. Return exactly one label per frame ({n} labels). You only classify frames; you do not judge the repair.
