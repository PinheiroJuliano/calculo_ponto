package state

import (
	"sync"
	"time"

	"calculo_ponto/internal/calculator"
	"calculo_ponto/internal/timer"
)

type AppState struct {
	mu          sync.Mutex
	Timer       *timer.SowonTimer
	CornerIndex int // 0: Top-Right, 1: Bottom-Right, 2: Bottom-Left, 3: Top-Left
}

var globalState *AppState
var once sync.Once

func GetState() *AppState {
	once.Do(func() {
		globalState = &AppState{
			Timer:       timer.NewSowonTimer(timer.ModeCountdown),
			CornerIndex: 0,
		}
	})
	return globalState
}

func (s *AppState) TogglePause() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Timer.TogglePause()
	if s.Timer.Paused {
		return "Cronômetro PAUSADO [Pressione ESPAÇO para retomar]"
	}
	return "Cronômetro EM EXECUÇÃO"
}

func (s *AppState) ResetTimer() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Timer.Reset()
	return "Cronômetro REINICIADO!"
}

func (s *AppState) SetMode(m timer.Mode) string {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.Timer.Mode = m
	return "Modo alterado para: " + m.String()
}

func (s *AppState) CycleCorner() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.CornerIndex = (s.CornerIndex + 1) % 4
	names := []string{"Canto Superior Direito", "Canto Inferior Direito", "Canto Inferior Esquerdo", "Canto Superior Esquerdo"}
	return "Overlay movido para: " + names[s.CornerIndex]
}

func (s *AppState) GetCornerIndex() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.CornerIndex
}

func (s *AppState) GetFormattedDisplay(res calculator.ShiftResult, agora time.Time) (string, timer.Mode, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.Timer.GetFormattedDisplay(res, agora), s.Timer.Mode, s.Timer.Paused
}
