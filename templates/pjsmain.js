draw = function() {
    background(0);
    fill(255);
    text(JSON.stringify(world) + width + ", " + height, 0, 0, width, height);
    
    if(mouseIsPressed && keyIsPressed) {
        fill(255, 0, 0);
    } else if(mouseIsPressed) {
        fill(0, 255, 0);
    } else if(keyIsPressed) {
        fill(0, 0, 255);
    }

    ellipse(mouseX, mouseY, 20, 20);
};