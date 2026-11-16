#include "lab_os.h"

enum { WIDTH = 10, HEIGHT = 8, WALL_COUNT = 24, DURATION = 60000, TARGET = 1 };

static const uint8_t walls[WALL_COUNT][2] = {
    {1,2}, {1,5}, {2,4}, {2,5}, {3,0}, {3,1},
    {3,2}, {3,5}, {3,6}, {4,1}, {4,2}, {4,3},
    {4,4}, {5,0}, {5,1}, {5,2}, {5,4}, {7,4},
    {7,5}, {8,2}, {8,3}, {9,0}, {9,2}, {9,4}
};
static const int32_t phase_colors[4] = {31727, 2047, 2016, 63488};
static int32_t phase;
static int32_t score;
static int32_t player_x;
static int32_t player_y;
static uint32_t elapsed;
static uint32_t rng;
static uint32_t timer_accumulator;
static int32_t hazard_exists;
static int32_t hazard_x;
static int32_t hazard_y;

static void reset_game(void)
{
    phase = 0;
    score = 0;
    elapsed = 0;
    player_x = 0;
    player_y = 0;
    rng = 739;
    timer_accumulator = 0;
    hazard_exists = 0;
    hazard_x = 0;
    hazard_y = 0;
}

static int32_t blocked(int32_t x, int32_t y)
{
    int32_t i;
    if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) {
        return 1;
    }
    for (i = 0; i < WALL_COUNT; i++) {
        if (walls[i][0] == x && walls[i][1] == y) {
            return 1;
        }
    }
    return 0;
}

static void draw_game(void)
{
    int32_t i;
    int32_t cell = 280 / WIDTH;
    if (160 / HEIGHT < cell) {
        cell = 160 / HEIGHT;
    }
    rect(0, 0, 320, 240, 2113);
    rect(20, 16, 280, 8, phase_colors[phase]);
    for (i = 0; i < WALL_COUNT; i++) {
        rect(21 + walls[i][0] * cell,
             49 + walls[i][1] * cell,
             cell - 2, cell - 2, 27469);
    }
    rect(22 + 9 * cell, 50 + 7 * cell,
         cell - 4, cell - 4, 63519);
    rect(23 + player_x * cell, 51 + player_y * cell,
         cell - 6, cell - 6, 2016);
    if (score > 0) {
        rect(20, 224, 280 * score / TARGET, 6, 65504);
    }
}

uint32_t sdk_abi(void)
{
    return 2;
}

void init(void)
{
    reset_game();
}

void shutdown(uint32_t reason)
{
    (void)reason;
}

int32_t tick(uint32_t held, uint32_t pressed, uint32_t released, uint32_t dt)
{
    int32_t next_x;
    int32_t next_y;
    (void)held;
    (void)released;

    if (pressed & BACK) {
        return 1;
    }
    if (pressed & RESET) {
        reset_game();
        draw_game();
        return 0;
    }
    if (phase == 0) {
        if (pressed & START) {
            phase = 1;
        }
        draw_game();
        return 0;
    }
    if (phase == 2 || phase == 3) {
        draw_game();
        return 0;
    }

    if (dt >= DURATION - elapsed) {
        elapsed = DURATION;
        phase = 3;
        draw_game();
        return 0;
    }
    elapsed += dt;

    next_x = player_x;
    next_y = player_y;
    if (pressed & RIGHT) {
        next_x++;
    } else if (pressed & LEFT) {
        next_x--;
    } else if (pressed & DOWN) {
        next_y++;
    } else if (pressed & UP) {
        next_y--;
    }
    if (!blocked(next_x, next_y)) {
        player_x = next_x;
        player_y = next_y;
    }
    if (player_x == 9 && player_y == 7) {
        score = 1;
        phase = 2;
    }
    draw_game();
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

int32_t debug_elapsed(void)
{
    return (int32_t)elapsed;
}
