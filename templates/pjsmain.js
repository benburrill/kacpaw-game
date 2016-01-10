register_control_handler(function(data) {
    $("#comment-output").text("move " + data.direction);
});


textAlign(CENTER, BOTTOM);

draw = function() {
    background(0);
    world.players.forEach(function(player) {
        var x = player.x * width,
            y = player.y * height;

        fill(255);
        text(player.name, x, y - player.radius);
        
        fill(player.color);
        ellipse(x, y, player.radius * 2, player.radius * 2);
    });
};