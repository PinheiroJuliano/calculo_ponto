package timer

import (
	"time"

	"calculo_ponto/internal/calculator"
)

type Mode int

const (
	ModeCountdown Mode = iota // Contagem regressiva até a saída
	ModeStopwatch             // Cronômetro progressivo desde a entrada
	ModeClock                 // Relógio em tempo real HH:MM:SS
)

func (m Mode) String() string {
	switch m {
	case ModeCountdown:
		return "Contagem Regressiva (Saída)"
	case ModeStopwatch:
		return "Tempo Trabalhado (Stopwatch)"
	case ModeClock:
		return "Relógio em Tempo Real"
	default:
		return "Desconhecido"
	}
}

type SowonTimer struct {
	Mode      Mode
	Paused    bool
	StartTime time.Time
	PauseTime time.Time
	PausedDur time.Duration
}

func NewSowonTimer(mode Mode) *SowonTimer {
	return &SowonTimer{
		Mode:      mode,
		Paused:    false,
		StartTime: time.Now(),
	}
}

func (t *SowonTimer) TogglePause() {
	if t.Paused {
		// Retomando
		t.PausedDur += time.Since(t.PauseTime)
		t.Paused = false
	} else {
		// Pausando
		t.PauseTime = time.Now()
		t.Paused = true
	}
}

func (t *SowonTimer) Reset() {
	t.StartTime = time.Now()
	t.PausedDur = 0
	t.Paused = false
}

// GetFormattedDisplay calcula a string HH:MM:SS para exibição de acordo com o modo ativo.
func (t *SowonTimer) GetFormattedDisplay(res calculator.ShiftResult, agora time.Time) string {
	switch t.Mode {
	case ModeClock:
		return agora.Format("15:04:05")

	case ModeCountdown:
		// Exibe quanto falta para a saída (ou tempo extra se já passou)
		if res.IsHoraExtra {
			return "-" + calculator.FormatDuration(res.Restante)
		}
		return calculator.FormatDuration(res.Restante)

	case ModeStopwatch:
		// Exibe tempo total transcorrido desde o horário de entrada
		if agora.Before(res.EntradaTime) {
			return "00:00:00"
		}
		trabalhado := agora.Sub(res.EntradaTime)
		return calculator.FormatDuration(trabalhado)

	default:
		return "00:00:00"
	}
}
