NAME = AICM
DESCRIPTION = "Intro Ciencia Materiais"
COMPRESSED = YES
ARCHIVED = YES

SRC = src/main.c src/ui.c src/catalog_teoria.c src/catalog_exercicios.c

CFLAGS = -Wall -Wextra -Oz
LDFLAGS = -lgraphx -lkeypadc -lm

include $(shell cedev-config --makefile)
