#include "app.h"

#include <graphx.h>
#include <keypadc.h>
#include <stdlib.h>
#include <string.h>
#include <tice.h>

static void print_clip(const char *s, int x, int y, uint8_t max_cols) {
    char buf[SCREEN_COLS + 1];
    uint8_t i = 0;
    while (s[i] && i < max_cols && i < SCREEN_COLS) {
        buf[i] = s[i];
        i++;
    }
    buf[i] = '\0';
    gfx_PrintStringXY(buf, x, y);
}

static void prn(const char *s, int x, int y) {
    print_clip(s, x, y, SCREEN_COLS);
}

static void print_center(const char *text, int y) {
    unsigned int w = gfx_GetStringWidth(text);
    int x = (SCREEN_W - (int)w) / 2;
    if (x < 0) {
        x = 0;
    }
    prn(text, x, y);
}

void ui_init(void) {
    kb_DisableOnLatch();
    kb_Scan();

    gfx_Begin();
    gfx_SetDrawBuffer();

    gfx_palette[COL_WHITE] = gfx_RGBTo1555(255, 255, 255);
    gfx_palette[COL_BLACK] = gfx_RGBTo1555(0, 0, 0);
    gfx_palette[COL_GRAY] = gfx_RGBTo1555(145, 145, 145);
    gfx_palette[COL_LIGHT] = gfx_RGBTo1555(228, 236, 244);
    gfx_palette[COL_BLUE] = gfx_RGBTo1555(35, 76, 150);
    gfx_palette[COL_RED] = gfx_RGBTo1555(190, 36, 36);
    gfx_palette[COL_GREEN] = gfx_RGBTo1555(34, 128, 82);

    gfx_FillScreen(COL_WHITE);
    gfx_SwapDraw();
    gfx_FillScreen(COL_WHITE);
    gfx_SwapDraw();
    gfx_SetDrawBuffer();
    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    gfx_SetTextBGColor(COL_WHITE);
    gfx_SetTextTransparentColor(COL_WHITE);
    gfx_SetTextScale(1, 1);
}

void check_on_exit(void) {
    kb_Scan();
    if (kb_On) {
        gfx_End();
        exit(0);
    }
}

uint8_t pressed_once(kb_lkey_t key) {
    static uint8_t prev[8];
    uint8_t group = (uint8_t)(key >> 8);
    uint8_t mask = (uint8_t)(key & 0xFF);
    uint8_t down = kb_IsDown(key) ? 1 : 0;
    uint8_t edge;

    if (group >= 8) {
        return 0;
    }

    edge = (down && !(prev[group] & mask)) ? 1 : 0;
    if (down) {
        prev[group] |= mask;
    } else {
        prev[group] &= (uint8_t)~mask;
    }
    return edge;
}

void wait_key_release(void) {
    do {
        check_on_exit();
        kb_Scan();
    } while (kb_Data[1] | kb_Data[2] | kb_Data[3] |
             kb_Data[4] | kb_Data[5] | kb_Data[6] | kb_Data[7]);
    delay(20);
}

static void draw_menu_row(int y, const char *text, uint8_t selected) {
    if (selected) {
        gfx_SetColor(COL_LIGHT);
        gfx_FillRectangle(12, y - 3, 296, 15);
        gfx_SetColor(COL_BLUE);
        gfx_Rectangle(12, y - 3, 296, 15);
        gfx_SetTextFGColor(COL_BLUE);
    } else {
        gfx_SetTextFGColor(COL_BLACK);
    }
    prn(text, 22, y);
}

void draw_main_menu(uint8_t selected) {
    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    print_center("AICM", 8);
    gfx_SetColor(COL_BLACK);
    gfx_HorizLine(0, 24, SCREEN_W);
    gfx_SetTextFGColor(COL_GRAY);
    prn("Assunto:", 10, 30);

    draw_menu_row(54, "1. Teoria", selected == 0);
    draw_menu_row(74, "2. Exercicios", selected == 1);

    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(0, 224, SCREEN_W);
    gfx_SetTextFGColor(COL_BLACK);
    prn("UP/DOWN escolhe ENTER abre ON sair", 2, 229);
}

void draw_topic_menu(const Group *group, uint8_t selected, uint8_t top) {
    uint8_t i;
    uint8_t max = group->topic_count - top;

    if (max > MENU_VISIBLE) {
        max = MENU_VISIBLE;
    }

    gfx_FillScreen(COL_WHITE);
    gfx_SetTextFGColor(COL_BLACK);
    print_center(group->title, 8);
    gfx_SetColor(COL_BLACK);
    gfx_HorizLine(0, 24, SCREEN_W);
    gfx_SetTextFGColor(COL_GRAY);
    prn("Escolha o bloco:", 10, 30);

    for (i = 0; i < max; i++) {
        uint8_t idx = top + i;
        int y = 46 + i * 17;
        draw_menu_row(y, group->topics[idx].name, idx == selected);
    }

    gfx_SetTextFGColor(COL_BLACK);
    if (top > 0) {
        prn("^", 300, 32);
    }
    if (top + max < group->topic_count) {
        prn("v", 300, 212);
    }
    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(0, 224, SCREEN_W);
    gfx_SetTextFGColor(COL_BLACK);
    prn("UP/DOWN escolhe ENTER abre ON sair", 2, 229);
}

static void draw_ex_header(const char *topic, const char *ex_title,
                           uint8_t ex, uint8_t ex_total,
                           uint8_t page, uint8_t page_total) {
    char meta[21];
    uint8_t pos = 0;
    uint8_t n;

    gfx_FillScreen(COL_WHITE);
    gfx_SetColor(COL_BLACK);
    gfx_SetTextFGColor(COL_BLACK);
    prn(topic, 2, 2);
    meta[pos++] = 'E';
    meta[pos++] = 'x';
    meta[pos++] = ' ';
    n = (uint8_t)(ex + 1);
    if (n >= 10) meta[pos++] = (char)('0' + n / 10);
    meta[pos++] = (char)('0' + n % 10);
    meta[pos++] = '/';
    if (ex_total >= 10) meta[pos++] = (char)('0' + ex_total / 10);
    meta[pos++] = (char)('0' + ex_total % 10);
    meta[pos++] = ' ';
    meta[pos++] = 'P';
    meta[pos++] = 'g';
    meta[pos++] = ' ';
    n = (uint8_t)(page + 1);
    if (n >= 10) meta[pos++] = (char)('0' + n / 10);
    meta[pos++] = (char)('0' + n % 10);
    meta[pos++] = '/';
    if (page_total >= 10) meta[pos++] = (char)('0' + page_total / 10);
    meta[pos++] = (char)('0' + page_total % 10);
    meta[pos] = '\0';
    prn(meta, 190, 2);
    gfx_HorizLine(0, 14, SCREEN_W);

    gfx_SetTextFGColor(COL_GRAY);
    prn(ex_title, 8, 18);
    gfx_SetTextFGColor(COL_BLACK);
}

static void result_box(const char *text, int y) {
    gfx_SetColor(COL_BLUE);
    gfx_Rectangle(24, y, 272, 30);
    gfx_Rectangle(25, y + 1, 270, 28);
    gfx_SetTextFGColor(COL_BLUE);
    print_center(text, y + 10);
    gfx_SetTextFGColor(COL_BLACK);
}

void draw_exercise_view(const Topic *topic, uint8_t ex, uint8_t page) {
    const Exercise *exercise = &topic->items[ex];
    const Page *cur = &exercise->pages[page];
    uint8_t i;

    draw_ex_header(topic->name, exercise->title, ex, topic->count,
                   page, exercise->page_count);

    if (cur->title) {
        print_center(cur->title, 30);
    }
    if (cur->subtitle) {
        gfx_SetTextFGColor(COL_GRAY);
        print_center(cur->subtitle, 44);
        gfx_SetTextFGColor(COL_BLACK);
    }

    if (cur->body) {
        cur->body();
    }

    for (i = 0; i < cur->line_count; i++) {
        gfx_SetTextFGColor(cur->lines[i].color);
        prn(cur->lines[i].text, cur->lines[i].x, cur->lines[i].y);
    }

    if (cur->result) {
        result_box(cur->result, cur->result_y);
    }
    gfx_SetTextFGColor(COL_BLACK);

    gfx_SetColor(COL_GRAY);
    gfx_HorizLine(0, 224, SCREEN_W);
    gfx_SetTextFGColor(COL_BLACK);
    prn("UP/DN ex  </> pg  CLEAR volta ON sair", 2, 229);
}

/* ----- plot / drawing primitives for generated body functions ----- */

void g_line(int x1, int y1, int x2, int y2, uint8_t color) {
    gfx_SetColor(color);
    gfx_Line(x1, y1, x2, y2);
}

void g_dash(int x1, int y1, int x2, int y2, uint8_t color) {
    int dx = x2 - x1;
    int dy = y2 - y1;
    int adx = dx < 0 ? -dx : dx;
    int ady = dy < 0 ? -dy : dy;
    int steps = (adx > ady ? adx : ady);
    int i;
    if (steps == 0) return;
    gfx_SetColor(color);
    for (i = 0; i <= steps; i++) {
        if (((i / 3) & 1) == 0) {
            int px = x1 + dx * i / steps;
            int py = y1 + dy * i / steps;
            gfx_SetPixel(px, py);
        }
    }
}

void g_dot(int x, int y, uint8_t color) {
    gfx_SetColor(color);
    gfx_FillCircle(x, y, 2);
}

void g_circ(int x, int y, int r, uint8_t color) {
    gfx_SetColor(color);
    gfx_Circle(x, y, r);
}

void g_disc(int x, int y, int r, uint8_t color) {
    gfx_SetColor(color);
    gfx_FillCircle(x, y, r);
    gfx_SetColor(COL_BLACK);
    gfx_Circle(x, y, r);
}

void g_text(const char *s, int x, int y, uint8_t color) {
    gfx_SetTextFGColor(color);
    prn(s, x, y);
    gfx_SetTextFGColor(COL_BLACK);
}

void g_axes(int x0, int y0, int x1, int y1) {
    /* y-axis (vertical) at x0 from y0(top) to y1(bottom); x-axis at y1 */
    gfx_SetColor(COL_BLACK);
    gfx_Line(x0, y0, x0, y1);
    gfx_Line(x0, y1, x1, y1);
    /* arrow heads */
    gfx_Line(x0, y0, x0 - 3, y0 + 6);
    gfx_Line(x0, y0, x0 + 3, y0 + 6);
    gfx_Line(x1, y1, x1 - 6, y1 - 3);
    gfx_Line(x1, y1, x1 - 6, y1 + 3);
}
