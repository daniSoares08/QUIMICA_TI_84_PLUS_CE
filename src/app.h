#ifndef APP_H
#define APP_H

#include <stdint.h>
#include <stdbool.h>
#include <keypadc.h>

#define SCREEN_W 320
#define SCREEN_H 240
#define SCREEN_COLS 39
#define MENU_VISIBLE 10

enum {
    COL_WHITE = 0,
    COL_BLACK = 1,
    COL_GRAY = 2,
    COL_LIGHT = 3,
    COL_BLUE = 4,
    COL_RED = 5,
    COL_GREEN = 6
};

typedef void (*body_draw_fn)(void);

typedef struct {
    const char *text;
    int x;
    int y;
    uint8_t color;
} TextLine;

typedef struct {
    const char *title;
    const char *subtitle;
    const TextLine *lines;
    uint8_t line_count;
    const char *result;
    uint8_t result_y;
    body_draw_fn body;
} Page;

typedef struct {
    const char *title;
    const Page *pages;
    uint8_t page_count;
} Exercise;

typedef struct {
    const char *name;
    const Exercise *items;
    uint8_t count;
} Topic;

typedef struct {
    const char *title;
    const Topic *topics;
    uint8_t topic_count;
} Group;

extern const Group teoria_group;
extern const Group exerc_group;

/* ui + input */
void ui_init(void);
void check_on_exit(void);
uint8_t pressed_once(kb_lkey_t key);
void wait_key_release(void);

void draw_main_menu(uint8_t selected);
void draw_topic_menu(const Group *group, uint8_t selected, uint8_t top);
void draw_exercise_view(const Topic *topic, uint8_t ex, uint8_t page);

/* plot/draw primitives used by generated body functions */
void g_line(int x1, int y1, int x2, int y2, uint8_t color);
void g_dash(int x1, int y1, int x2, int y2, uint8_t color);
void g_dot(int x, int y, uint8_t color);
void g_circ(int x, int y, int r, uint8_t color);
void g_disc(int x, int y, int r, uint8_t color);
void g_text(const char *s, int x, int y, uint8_t color);
void g_axes(int x0, int y0, int x1, int y1);

#endif
