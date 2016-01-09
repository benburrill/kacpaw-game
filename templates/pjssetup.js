// I could maybe use the setup function here, but the setup function is horrible.  You can't even make a pure js setup function because (presumably) pjs searches the source for ``void setup`` to find the right code to run.

// sets the size to the canvas's size
var on_resize = function() {
    $canvas = $("#output-canvas");
    size($canvas.width(), $canvas.height());
};

// automatically resize as the window resizes
$(window).resize(on_resize);
// resize once at startup to initialize size
on_resize();

// Let's make our environment more like KA's version of PJS.  Why not, right?
background(255);

Object.defineProperty(this, "mouseIsPressed", {
    get: function() {
        return __mousePressed;
    }
});

Object.defineProperty(this, "keyIsPressed", {
    get: function() {
        return __keyPressed;
    }
});

// todo: maybe mimic more stuff like getImage from https://khanacademy.zendesk.com/hc/en-us/articles/202260404-Which-parts-of-ProcessingJS-does-Khan-Academy-support-

var register_control_handler = function(func) {
    $("#controls").submit(function(event) {
        func(_.object(
            _.chain(["name", "value"]).map(_.property) // property getters for "name" and "value"
            .map(_.partial(_.map, event.target.elements)) // _.map(elements, ...) for each of them
            .unzip().value() // convert into [name, value] pairs
        ), event); // pass in the actual event, in case anyone wants to use it

        event.preventDefault();
    });
};

register_control_handler(console.log.bind(console)); // for debugging