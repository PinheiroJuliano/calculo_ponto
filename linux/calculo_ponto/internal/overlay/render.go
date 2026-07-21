package overlay

import (
	"image"
	"image/color"
	"math"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"golang.org/x/image/font"
	"golang.org/x/image/font/basicfont"
	"golang.org/x/image/math/fixed"
)

// GetThemeColor retorna a cor principal do tema ativo.
func GetThemeColor(theme string) color.RGBA {
	switch theme {
	case "green":
		return color.RGBA{0, 255, 102, 255} // Matrix Green
	case "pink":
		return color.RGBA{255, 0, 127, 255} // Cyberpunk Pink
	case "amber":
		return color.RGBA{255, 179, 0, 255} // Amber Gold
	case "white":
		return color.RGBA{255, 255, 255, 255} // Minimal White
	default:
		return color.RGBA{0, 229, 255, 255} // Cyan Futurista (Padrão)
	}
}

// Define quais segmentos (a..g) pertencem a cada caractere
var segmentMap = map[rune][7]bool{
	'0': {true, true, true, true, true, true, false},
	'1': {false, true, true, false, false, false, false},
	'2': {true, true, false, true, true, false, true},
	'3': {true, true, true, true, false, false, true},
	'4': {false, true, true, false, false, true, true},
	'5': {true, false, true, true, false, true, true},
	'6': {true, false, true, true, true, true, true},
	'7': {true, true, true, false, false, false, false},
	'8': {true, true, true, true, true, true, true},
	'9': {true, true, true, true, false, true, true},
	'-': {false, false, false, false, false, false, true},
}

// Draw7SegmentDigit desenha um único dígito de 7 segmentos em (x, y) com a largura (w) e altura (h) dadas.
func Draw7SegmentDigit(screen *ebiten.Image, char rune, x, y, w, h float32, activeColor, inactiveColor color.Color) {
	thickness := w * 0.16
	padding := thickness * 0.2

	halfH := (h - thickness) / 2

	// Posições dos segmentos:
	// a: topo horizontal
	// b: topo direita vertical
	// c: baixo direita vertical
	// d: base horizontal
	// e: baixo esquerda vertical
	// f: topo esquerda vertical
	// g: meio horizontal

	segments := [7][4]float32{
		// a (topo horiz)
		{x + thickness, y, w - 2*thickness, thickness},
		// b (topo dir vert)
		{x + w - thickness, y + thickness, thickness, halfH - thickness/2},
		// c (baixo dir vert)
		{x + w - thickness, y + halfH + thickness/2, thickness, halfH - thickness/2},
		// d (base horiz)
		{x + thickness, y + h - thickness, w - 2*thickness, thickness},
		// e (baixo esq vert)
		{x, y + halfH + thickness/2, thickness, halfH - thickness/2},
		// f (topo esq vert)
		{x, y + thickness, thickness, halfH - thickness/2},
		// g (meio horiz)
		{x + thickness, y + halfH - thickness/2, w - 2*thickness, thickness},
	}

	flags, isDigit := segmentMap[char]

	for i := 0; i < 7; i++ {
		seg := segments[i]
		col := inactiveColor
		if isDigit && flags[i] {
			col = activeColor
		}
		vector.DrawFilledRect(screen, seg[0]+padding, seg[1]+padding, seg[2]-2*padding, seg[3]-2*padding, col, true)
	}
}

// DrawColon desenha os dois pontos ":" do relógio.
func DrawColon(screen *ebiten.Image, x, y, w, h float32, activeColor color.Color, tickSec float64) {
	dotSize := w * 0.25
	cx := x + (w-dotSize)/2
	y1 := y + h*0.3 - dotSize/2
	y2 := y + h*0.7 - dotSize/2

	// Efeito piscar sutil
	alpha := 0.4 + 0.6*math.Abs(math.Sin(tickSec*math.Pi))
	r, g, b, _ := activeColor.RGBA()
	blinkingCol := color.RGBA{uint8(r >> 8), uint8(g >> 8), uint8(b >> 8), uint8(alpha * 255)}

	vector.DrawFilledRect(screen, cx, y1, dotSize, dotSize, blinkingCol, true)
	vector.DrawFilledRect(screen, cx, y2, dotSize, dotSize, blinkingCol, true)
}

// DrawText desenha texto básico na tela.
func DrawText(screen *ebiten.Image, str string, x, y int, col color.Color) {
	d := &font.Drawer{
		Dst:  screen,
		Src:  image.NewUniform(col),
		Face: basicfont.Face7x13,
		Dot:  fixed.Point26_6{X: fixed.I(x), Y: fixed.I(y)},
	}
	d.DrawString(str)
}
