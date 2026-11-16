#include "lab_os.h"

static int32_t phase;
static int32_t score;
static int32_t player_x;
static int32_t player_y;
static uint32_t elapsed;
static uint32_t collected;
static uint32_t rng;
static uint32_t accumulator;
static int32_t hazard_exists;
static int32_t hazard_x;
static int32_t hazard_y;

static const int32_t wall_x[8] = {3, 3, 3, 5, 6, 7, 1, 2};
static const int32_t wall_y[8] = {1, 2, 3, 4, 4, 4, 5, 5};
static const int32_t coin_x[5] = {7, 1, 5, 6, 8};
static const int32_t coin_y[5] = {1, 3, 2, 5, 6};

static void reset_state(void)
{
    phase = 0;
    score = 0;
    player_x = 1;
    player_y = 1;
    elapsed = 0;
    collected = 0;
    rng = 1129;
    accumulator = 0;
    hazard_exists = 0;
    hazard_x = 0;
    hazard_y = 0;
}

static int32_t blocked(int32_t x, int32_t y)
{
    int32_t i;
    if (x < 0 || x >= 9 || y < 0 || y >= 7) {
        return 1;
    }
    for (i = 0; i < 8; i++) {
        if (wall_x[i] == x && wall_y[i] == y) {
            return 1;
        }
    }
    return 0;
}

static void draw(void)
{
    int32_t i;
    int32_t cell = 280 / 9;
    int32_t status_color = 31727;
    if (160 / 7 < cell) {
        cell = 160 / 7;
    }
    if (phase == 1) {
        status_color = 2047;
    } else if (phase == 2) {
        status_color = 2016;
    } else if (phase == 3) {
        status_color = 63488;
    }

    rect(0, 0, 320, 240, 2113);
    rect(20, 16, 280, 8, status_color);
    for (i = 0; i < 8; i++) {
        rect(21 + wall_x[i] * cell, 49 + wall_y[i] * cell,
             cell - 2, cell - 2, 27469);
    }
    for (i = 0; i < 5; i++) {
        if ((collected & (1u << i)) == 0) {
            rect(20 + coin_x[i] * cell + cell / 3,
                 48 + coin_y[i] * cell + cell / 3,
                 cell / 3, cell / 3, 65504);
        }
    }
    rect(23 + player_x * cell, 51 + player_y * cell,
         cell - 6, cell - 6, 2016);
    if (score > 0) {
        rect(20, 224, 280 * score / 5, 6, 65504);
    }
}

uint32_t sdk_abi(void)
{
    return 2;
}

void init(void)
{
    reset_state();
}

void shutdown(uint32_t reason)
{
    (void)reason;
}

int32_t tick(uint32_t held, uint32_t pressed, uint32_t released, uint32_t dt)
{
    int32_t next_x;
    int32_t next_y;
    int32_t i;

    if ((pressed & BACK) != 0) {
        return 1;
    }
    if ((pressed & RESET) != 0) {
        reset_state();
        draw();
        return 0;
    }
    (void)held;
    (void)released;

    if (phase == 0) {
        if ((pressed & START) != 0) {
            phase = 1;
        }
        draw();
        return 0;
    }
    if (phase != 1) {
        draw();
        return 0;
    }

    if (dt >= 60000u - elapsed) {
        elapsed = 60000;
        phase = 3;
        draw();
        return 0;
    }
    elapsed += dt;

    next_x = player_x;
    next_y = player_y;
    if ((pressed & RIGHT) != 0) {
        next_x++;
    } else if ((pressed & LEFT) != 0) {
        next_x--;
    } else if ((pressed & DOWN) != 0) {
        next_y++;
    } else if ((pressed & UP) != 0) {
        next_y--;
    }
    if (!blocked(next_x, next_y)) {
        player_x = next_x;
        player_y = next_y;
    }

    for (i = 0; i < 5; i++) {
        if ((collected & (1u << i)) == 0 &&
            player_x == coin_x[i] && player_y == coin_y[i]) {
            collected |= 1u << i;
            score++;
        }
    }
    if (score == 5) {
        phase = 2;
    }
    draw();
    return 0;
}

int32_t debug_value(void)
{
    return (phase << 16) | score;
}

int32_t debug_x(void)
{
    return player_x;
}

int32_t debug_y(void)
{
    return player_y;
}

uint32_t debug_elapsed(void)
{
    return elapsed;
}
