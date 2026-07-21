package calculator

import (
	"testing"
	"time"
)

func TestCalculateNormal(t *testing.T) {
	cfg := ShiftConfig{
		Entrada: "08:00",
		Almoco:  60,
		Jornada: 8.0,
	}

	// 08:00 + 8h jornada + 1h (60min) almoço = 17:00
	agora := time.Date(2026, 7, 20, 10, 0, 0, 0, time.Local)

	res, err := Calculate(cfg, agora)
	if err != nil {
		t.Fatalf("Erro inesperado: %v", err)
	}

	saidaDesejada := time.Date(2026, 7, 20, 17, 0, 0, 0, time.Local)
	if !res.SaidaPrevista.Equal(saidaDesejada) {
		t.Errorf("SaidaPrevista esperada %v, obteve %v", saidaDesejada.Format("15:04"), res.SaidaPrevista.Format("15:04"))
	}

	if res.IsHoraExtra {
		t.Errorf("Esperava IsHoraExtra == false às 10:00")
	}

	expectedRestante := 7 * time.Hour
	if res.Restante != expectedRestante {
		t.Errorf("Tempo restante esperado %v, obteve %v", expectedRestante, res.Restante)
	}
}

func TestCalculateHoraExtra(t *testing.T) {
	cfg := ShiftConfig{
		Entrada: "08:00",
		Almoco:  60,
		Jornada: 8.0,
	}

	// Agora é 18:30 -> Saída era 17:00, logo 1h30min de hora extra
	agora := time.Date(2026, 7, 20, 18, 30, 0, 0, time.Local)

	res, err := Calculate(cfg, agora)
	if err != nil {
		t.Fatalf("Erro inesperado: %v", err)
	}

	if !res.IsHoraExtra {
		t.Errorf("Esperava IsHoraExtra == true às 18:30")
	}

	expectedExtra := 90 * time.Minute
	if res.Restante != expectedExtra {
		t.Errorf("Hora extra esperada %v, obteve %v", expectedExtra, res.Restante)
	}
}

func TestCalculateInvalidInput(t *testing.T) {
	cfg := ShiftConfig{
		Entrada: "invalid",
		Almoco:  60,
		Jornada: 8.0,
	}

	agora := time.Now()
	_, err := Calculate(cfg, agora)
	if err == nil {
		t.Errorf("Esperava erro para entrada de horário inválida")
	}
}
