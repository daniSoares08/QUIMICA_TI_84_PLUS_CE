#include "app.h"

#include <graphx.h>
#include <keypadc.h>
#include <stdbool.h>
#include <tice.h>

static void exercise_loop(const Topic *topic) {
    uint8_t ex = 0;
    uint8_t page = 0;
    bool redraw = true;

    wait_key_release();
    while (1) {
        const Exercise *exercise = &topic->items[ex];

        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_exercise_view(topic, ex, page);
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        if ((pressed_once(kb_KeyRight) || pressed_once(kb_KeyEnter)) &&
            page + 1 < exercise->page_count) {
            page++;
            redraw = true;
        }
        if (pressed_once(kb_KeyLeft) && page > 0) {
            page--;
            redraw = true;
        }
        if (pressed_once(kb_KeyDown) && ex + 1 < topic->count) {
            ex++;
            page = 0;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && ex > 0) {
            ex--;
            page = 0;
            redraw = true;
        }
        delay(20);
    }
}

static void group_loop(const Group *group) {
    uint8_t selected = 0;
    uint8_t top = 0;
    bool redraw = true;

    wait_key_release();
    while (1) {
        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_topic_menu(group, selected, top);
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) {
            wait_key_release();
            return;
        }
        if (pressed_once(kb_KeyEnter)) {
            exercise_loop(&group->topics[selected]);
            redraw = true;
        }
        if (pressed_once(kb_KeyDown) && selected + 1 < group->topic_count) {
            selected++;
            if (selected >= top + MENU_VISIBLE) {
                top++;
            }
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && selected > 0) {
            selected--;
            if (selected < top) {
                top--;
            }
            redraw = true;
        }
        delay(20);
    }
}

int main(void) {
    uint8_t selected = 0;
    bool redraw = true;

    ui_init();
    while (1) {
        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_main_menu(selected);
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyDown) && selected < 1) {
            selected++;
            redraw = true;
        }
        if (pressed_once(kb_KeyUp) && selected > 0) {
            selected--;
            redraw = true;
        }
        if (pressed_once(kb_KeyEnter)) {
            group_loop(selected == 0 ? &teoria_group : &exerc_group);
            redraw = true;
        }
        if (pressed_once(kb_Key1)) {
            selected = 0;
            group_loop(&teoria_group);
            redraw = true;
        }
        if (pressed_once(kb_Key2)) {
            selected = 1;
            group_loop(&exerc_group);
            redraw = true;
        }
        delay(20);
    }
}
