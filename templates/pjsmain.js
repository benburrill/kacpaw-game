register_control_handler(function(data) {
    $("#comment-output").text("move " + data.direction);
});


textAlign(CENTER, BOTTOM);

var player_radius = 25;

draw = function() {
    background(0);
    world.players.forEach(function(player) {
        var x = player.x * width,
            y = player.y * height;

        fill(255);
        text(player.name, x, y - player_radius);
        
        fill(0, 100, 0);
        ellipse(x, y, player_radius * 2, player_radius * 2);
    });
};