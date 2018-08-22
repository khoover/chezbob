var sounds = {};

sounds.init = function() {
    sounds.happy = new Audio("/sounds/happybeep.mp3");
    sounds.unhappy = new Audio("/sounds/unhappybeep.mp3");
    sounds.error = new Audio("/sounds/error.mp3");

    var first = true;
    $("body").on('keypress', function() {
        if (!first)
            return;

        first = false;
        sounds.happy.play();
        sounds.happy.pause();
        sounds.unhappy.play();
        sounds.unhappy.pause();
        sounds.error.play();
        sounds.error.pause();
    });
};

sounds.happy_beep = function() {
    sounds.happy.currentTime = 0;
    sounds.happy.play();
};

sounds.unhappy_beep = function() {
    sounds.unhappy.currentTime = 0;
    sounds.unhappy.play();
};

sounds.error_beep = function() {
    sounds.error.currentTime = 0;
    sounds.error.play();
};
