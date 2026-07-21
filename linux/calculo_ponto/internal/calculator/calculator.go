package calculator

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// ShiftConfig guarda os parâmetros da jornada de trabalho e customizações visuais.
type ShiftConfig struct {
	Entrada    string  `json:"entrada"`     // "HH:MM" ex: "08:00"
	Almoco     int     `json:"almoco"`      // Minutos ex: 60
	Jornada    float64 `json:"jornada"`     // Horas ex: 8.0
	Theme      string  `json:"theme"`       // "cyan", "green", "pink", "amber", "white"
	Opacity    float64 `json:"opacity"`     // Opacidade do fundo (0.0 a 1.0)
	ShowBorder bool    `json:"show_border"` // Exibir borda ao redor do overlay
}

// ShiftResult contém os resultados calculados do ponto.
type ShiftResult struct {
	EntradaTime   time.Time
	SaidaPrevista time.Time
	Restante      time.Duration
	IsHoraExtra   bool
}

// DefaultConfig retorna a configuração padrão se nenhuma estiver salva.
func DefaultConfig() ShiftConfig {
	return ShiftConfig{
		Entrada:    "08:00",
		Almoco:     60,
		Jornada:    8.0,
		Theme:      "cyan",
		Opacity:    0.75,
		ShowBorder: true,
	}
}

// Calculate calcula o horário de saída e o tempo restante/extra com base na hora de referência (agora).
func Calculate(cfg ShiftConfig, agora time.Time) (ShiftResult, error) {
	parts := strings.Split(strings.TrimSpace(cfg.Entrada), ":")
	if len(parts) != 2 {
		return ShiftResult{}, fmt.Errorf("formato de entrada inválido: use HH:MM")
	}

	hora, err := strconv.Atoi(parts[0])
	if err != nil || hora < 0 || hora > 23 {
		return ShiftResult{}, fmt.Errorf("hora de entrada inválida: %s", parts[0])
	}

	minuto, err := strconv.Atoi(parts[1])
	if err != nil || minuto < 0 || minuto > 59 {
		return ShiftResult{}, fmt.Errorf("minuto de entrada inválido: %s", parts[1])
	}

	if cfg.Almoco < 0 {
		return ShiftResult{}, fmt.Errorf("tempo de almoço inválido")
	}

	if cfg.Jornada <= 0 {
		return ShiftResult{}, fmt.Errorf("jornada de trabalho deve ser maior que zero")
	}

	// Define o horário de entrada para o mesmo dia de "agora"
	entradaTime := time.Date(
		agora.Year(), agora.Month(), agora.Day(),
		hora, minuto, 0, 0, agora.Location(),
	)

	// Duração da jornada em nanosegundos
	jornadaMinutos := int(cfg.Jornada * 60)
	duracaoTotal := time.Duration(jornadaMinutos+cfg.Almoco) * time.Minute

	saidaPrevista := entradaTime.Add(duracaoTotal)

	diff := saidaPrevista.Sub(agora)
	isExtra := diff < 0

	restante := diff
	if isExtra {
		restante = -diff
	}

	return ShiftResult{
		EntradaTime:   entradaTime,
		SaidaPrevista: saidaPrevista,
		Restante:      restante,
		IsHoraExtra:   isExtra,
	}, nil
}

// FormatDuration formata uma duração em HH:MM:SS com suporte a padding de 2 dígitos.
func FormatDuration(d time.Duration) string {
	totalSegundos := int(d.Seconds())
	h := totalSegundos / 3600
	m := (totalSegundos % 3600) / 60
	s := totalSegundos % 60
	return fmt.Sprintf("%02d:%02d:%02d", h, m, s)
}
