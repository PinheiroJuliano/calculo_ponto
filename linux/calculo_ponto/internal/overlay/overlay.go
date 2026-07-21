package overlay

import (
	"fmt"
	"image/color"
	"time"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/vector"

	"calculo_ponto/internal/calculator"
	"calculo_ponto/internal/config"
	"calculo_ponto/internal/state"
	"calculo_ponto/internal/timer"
)

const (
	WindowWidth  = 360
	WindowHeight = 120
)

type OverlayApp struct {
	cfg          calculator.ShiftConfig
	shiftResult  calculator.ShiftResult
	calcErr      error
	agora        time.Time
	appState     *state.AppState
	lastCorner   int
}

func NewOverlayApp() *OverlayApp {
	cfg := config.Load()
	agora := time.Now()
	res, err := calculator.Calculate(cfg, agora)
	st := state.GetState()

	return &OverlayApp{
		cfg:         cfg,
		shiftResult: res,
		calcErr:     err,
		agora:       agora,
		appState:    st,
		lastCorner:  st.GetCornerIndex(),
	}
}

func (app *OverlayApp) Update() error {
	app.agora = time.Now()

	// Recarrega configuração para sincronizar edições do terminal em tempo real
	app.cfg = config.Load()

	// Recalcula o ponto
	res, err := calculator.Calculate(app.cfg, app.agora)
	app.shiftResult = res
	app.calcErr = err

	// Verifica se o canto foi alterado via Terminal
	currentCorner := app.appState.GetCornerIndex()
	if currentCorner != app.lastCorner {
		app.lastCorner = currentCorner
		app.applyCornerPosition(currentCorner)
	}

	return nil
}

func (app *OverlayApp) applyCornerPosition(cornerIndex int) {
	sw, sh := ebiten.Monitor().Size()
	if sw <= 0 || sh <= 0 {
		return
	}

	switch cornerIndex {
	case 0: // Canto Superior Direito
		ebiten.SetWindowPosition(sw-WindowWidth-30, 40)
	case 1: // Canto Inferior Direito
		ebiten.SetWindowPosition(sw-WindowWidth-30, sh-WindowHeight-60)
	case 2: // Canto Inferior Esquerdo
		ebiten.SetWindowPosition(30, sh-WindowHeight-60)
	case 3: // Canto Superior Esquerdo
		ebiten.SetWindowPosition(30, 40)
	}
}

func (app *OverlayApp) Draw(screen *ebiten.Image) {
	// Limpa o buffer com transparência total (alpha 0)
	screen.Fill(color.RGBA{0, 0, 0, 0})

	// Fundo translúcido customizável (só desenha se opacidade > 0)
	alpha := uint8(app.cfg.Opacity * 255)
	if app.cfg.Opacity > 0 {
		bgColor := color.RGBA{18, 18, 24, alpha}
		vector.DrawFilledRect(screen, 0, 0, float32(WindowWidth), float32(WindowHeight), bgColor, true)
	}

	// Cor principal do Tema de Aparência
	themeCol := GetThemeColor(app.cfg.Theme)

	// Borda sutil de destaque (opcional)
	if app.cfg.ShowBorder {
		borderColor := color.RGBA{125, 86, 244, alpha}
		if app.shiftResult.IsHoraExtra {
			borderColor = color.RGBA{255, 69, 58, alpha} // Vermelho em Hora Extra
		}
		vector.StrokeRect(screen, 1, 1, float32(WindowWidth-2), float32(WindowHeight-2), 1.5, borderColor, true)
	}

	dispStr, activeMode, isPaused := app.appState.GetFormattedDisplay(app.shiftResult, app.agora)

	// Texto de Cabeçalho / Informações
	headerCol := color.RGBA{180, 180, 195, 255}
	modeText := activeMode.String()
	if isPaused {
		modeText += " [PAUSADO]"
	}

	saidaText := "Saida: --:--"
	if app.calcErr == nil {
		saidaText = fmt.Sprintf("Saida Prevista: %s", app.shiftResult.SaidaPrevista.Format("15:04"))
	}

	DrawText(screen, modeText, 12, 20, headerCol)
	DrawText(screen, saidaText, 210, 20, themeCol)

	// Cores dos dígitos 7-segmentos
	activeCol := themeCol // Tema selecionado
	if app.shiftResult.IsHoraExtra && activeMode == timer.ModeCountdown {
		activeCol = color.RGBA{255, 69, 58, 255} // Vermelho Alerta
	}
	if isPaused {
		activeCol = color.RGBA{255, 214, 10, 255} // Amarelo Pausa
	}
	inactiveCol := color.RGBA{30, 35, 45, 120}

	// Desenha a hora formatada em HH:MM:SS
	digitW := float32(30)
	digitH := float32(52)
	spacing := float32(6)
	startX := float32(16)
	startY := float32(34)

	secSec := float64(app.agora.UnixNano()) / 1e9

	for _, char := range dispStr {
		if char == ':' {
			DrawColon(screen, startX, startY, 18, digitH, activeCol, secSec)
			startX += 18 + spacing
		} else {
			Draw7SegmentDigit(screen, char, startX, startY, digitW, digitH, activeCol, inactiveCol)
			startX += digitW + spacing
		}
	}

	// Footer status (sem a label de controle via terminal)
	footerCol := color.RGBA{140, 140, 150, 255}
	footerText := "Faltam: " + calculator.FormatDuration(app.shiftResult.Restante)
	if app.shiftResult.IsHoraExtra {
		footerText = "Hora Extra: +" + calculator.FormatDuration(app.shiftResult.Restante)
		footerCol = color.RGBA{255, 69, 58, 255}
	}
	DrawText(screen, footerText, 12, 105, footerCol)
}

func (app *OverlayApp) Layout(outsideWidth, outsideHeight int) (int, int) {
	return WindowWidth, WindowHeight
}

// RunOverlay inicia a janela flutuante no desktop.
func RunOverlay() error {
	ebiten.SetWindowSize(WindowWidth, WindowHeight)
	ebiten.SetWindowTitle("Ponto & Sowon Overlay")
	ebiten.SetWindowDecorated(false)          // Sem bordas de janela
	ebiten.SetWindowFloating(true)           // ALWAYS ON TOP!
	ebiten.SetWindowMousePassthrough(true)    // Mouse passthrough
	ebiten.SetWindowResizingMode(ebiten.WindowResizingModeDisabled)
	ebiten.SetScreenClearedEveryFrame(false) // Permite transparência real de fundo no Ebitengine

	// Posiciona no canto superior direito por padrão para não atrapalhar no meio da tela
	sw, sh := ebiten.Monitor().Size()
	if sw > 0 && sh > 0 {
		ebiten.SetWindowPosition(sw-WindowWidth-30, 40)
	}

	app := NewOverlayApp()
	op := &ebiten.RunGameOptions{
		ScreenTransparent: true, // ATIVA A JANELA TRANSPARENTE REAL DE DESKTOP
	}
	return ebiten.RunGameWithOptions(app, op)
}
