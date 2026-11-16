#include "lab_os.h"

enum {
    WIDTH = 5,
    HEIGHT = 8,
    CELL = 20,
    DURATION_MS = 40000,
    STEP_MS = 350,
    TARGET = 3
};

static uint32_t phase;
static uint32_t score;
static uint32_t elapsed;
static uint32_t accumulator;
static uint32_t rng;
static int32_t player_x;
static int32_t player_y;
static int32_t hazard_x;
static int32_t hazard_y;
static int32_t hazard_exists;

static void reset_game(void)
{
    phase = 0u;
    score = 0u;
    elapsed = 0u;
    accumulator = 0u;
    rng = 2731u;
    player_x = 2;
    player_y = 7;
    hazard_x = 0;
    hazard_y = 0;
    hazard_exists = 0;
}

static void draw_game(void)
{
    int32_t status_color = 31727;
    if (phase == 1u) {
        status_color = 2047;
    } else if (phase == 2u) {
        status_color = 2016;
    } else if (phase == 3u) {
        status_color = 63488;
    }

    rect(0, 0, 320, 240, 2113);
    rect(20, 16, 280, 8, status_color);

    if (hazard_exists) {
        rect(23 + hazard_x * CELL, 51 + hazard_y * CELL,
             CELL - 6, CELL - 6, 63488);
    }

    rect(23 + player_x * CELL, 51 + player_y * CELL,
         CELL - 6, CELL - 6, 2016);

    if (score > 0u) {
        rect(20, 224, (int32_t)(280u * score / TARGET), 6, 65504);
    }
}

uint32_t sdk_abi(void)
{
    return 2u;
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
    uint32_t step;

    if ((pressed & BACK) != 0u) {
        return 1;
    }

    (void)held;
    (void)released;

    if ((pressed & RESET) != 0u) {
        reset_game();
        draw_game();
        return 0;
    }

    if (phase == 0u) {
        if ((pressed & START) != 0u) {
            phase = 1u;
        }
        draw_game();
        return 0;
    }

    if (phase != 1u) {
        draw_game();
        return 0;
    }

    if (dt >= DURATION_MS - elapsed) {
        elapsed = DURATION_MS;
        phase = 3u;
        draw_game();
        return 0;
    }
    elapsed += dt;

    if ((pressed & RIGHT) != 0u) {
        if (player_x < WIDTH - 1) {
            player_x += 1;
        }
    } else if ((pressed & LEFT) != 0u) {
        if (player_x > 0) {
            player_x -= 1;
        }
    }

    accumulator += dt;
    for (step = 0u;
         step < 173u && accumulator >= STEP_MS && phase == 1u;
         step += 1u) {
        accumulator -= STEP_MS;

        if (hazard_exists) {
            hazard_y += 1;
            if (hazard_y >= HEIGHT) {
                score += 1u;
                hazard_exists = 0;
                if (score == TARGET) {
                    phase = 2u;
                    break;
                }
            }
        }

        if (!hazard_exists) {
            rng = 1664525u * rng + 1013904223u;
            hazard_x = (int32_t)(rng % WIDTH);
            hazard_y = 0;
            hazard_exists = 1;
        }

        if (hazard_x == player_x && hazard_y == player_y) {
            phase = 3u;
        }
    }

    draw_game();
    return 0;
}

uint32_t debug_value(void)
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
