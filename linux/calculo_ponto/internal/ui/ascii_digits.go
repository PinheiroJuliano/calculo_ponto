package ui

import "strings"

// BigDigitGlyphs define a representação ASCII (5 linhas de altura) para cada caractere.
var glyphs = map[rune][5]string{
	'0': {
		"█████",
		"█   █",
		"█   █",
		"█   █",
		"█████",
	},
	'1': {
		"  ██ ",
		" ███ ",
		"  ██ ",
		"  ██ ",
		"█████",
	},
	'2': {
		"█████",
		"    █",
		"█████",
		"█    ",
		"█████",
	},
	'3': {
		"█████",
		"    █",
		"█████",
		"    █",
		"█████",
	},
	'4': {
		"█   █",
		"█   █",
		"█████",
		"    █",
		"    █",
	},
	'5': {
		"█████",
		"█    ",
		"█████",
		"    █",
		"█████",
	},
	'6': {
		"█████",
		"█    ",
		"█████",
		"█   █",
		"█████",
	},
	'7': {
		"█████",
		"    █",
		"   ██",
		"  ██ ",
		"  ██ ",
	},
	'8': {
		"█████",
		"█   █",
		"█████",
		"█   █",
		"█████",
	},
	'9': {
		"█████",
		"█   █",
		"█████",
		"    █",
		"█████",
	},
	':': {
		"     ",
		"  █  ",
		"     ",
		"  █  ",
		"     ",
	},
	'-': {
		"     ",
		"     ",
		"█████",
		"     ",
		"     ",
	},
	' ': {
		"     ",
		"     ",
		"     ",
		"     ",
		"     ",
	},
}

// RenderBigText recebe uma string como "08:15:30" e retorna a versão ASCII BigText com 5 linhas.
func RenderBigText(text string) string {
	var lines [5]strings.Builder

	for _, char := range text {
		g, exists := glyphs[char]
		if !exists {
			g = glyphs[' ']
		}
		for i := 0; i < 5; i++ {
			lines[i].WriteString(g[i])
			lines[i].WriteString("  ") // Espaçamento entre dígitos
		}
	}

	var result strings.Builder
	for i := 0; i < 5; i++ {
		result.WriteString(lines[i].String())
		if i < 4 {
			result.WriteString("\n")
		}
	}

	return result.String()
}
