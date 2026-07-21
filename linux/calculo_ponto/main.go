package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	tea "github.com/charmbracelet/bubbletea"

	"calculo_ponto/internal/calculator"
	"calculo_ponto/internal/config"
	"calculo_ponto/internal/overlay"
	"calculo_ponto/internal/ui"
)

func main() {
	entradaFlag := flag.String("entrada", "", "Hora de entrada no formato HH:MM (ex: 08:30)")
	almocoFlag := flag.Int("almoco", -1, "Duração do almoço em minutos (ex: 60)")
	jornadaFlag := flag.Float64("jornada", -1, "Duração da jornada em horas (ex: 8.0)")

	flag.Parse()

	// Se o usuário passou parâmetros diretamente pela linha de comando
	if *entradaFlag != "" || *almocoFlag >= 0 || *jornadaFlag > 0 {
		cfg := config.Load()
		if *entradaFlag != "" {
			cfg.Entrada = *entradaFlag
		}
		if *almocoFlag >= 0 {
			cfg.Almoco = *almocoFlag
		}
		if *jornadaFlag > 0 {
			cfg.Jornada = *jornadaFlag
		}

		// Valida
		if _, err := calculator.Calculate(cfg, time.Now()); err != nil {
			fmt.Printf("Erro nos parâmetros informados: %v\n", err)
			os.Exit(1)
		}

		if err := config.Save(cfg); err != nil {
			fmt.Printf("Erro ao salvar configurações: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Configurações atualizadas: Entrada=%s, Almoço=%dmin, Jornada=%.1fh\n", cfg.Entrada, cfg.Almoco, cfg.Jornada)
	}

	// Executa a TUI interativa no terminal em paralelo
	go func() {
		p := tea.NewProgram(ui.InitialModel(), tea.WithAltScreen())
		if _, err := p.Run(); err != nil {
			fmt.Printf("Erro ao rodar TUI: %v\n", err)
		}
		os.Exit(0)
	}()

	// Executa o Overlay Desktop Flutuante com o Cronômetro Sowon na Thread Principal
	if err := overlay.RunOverlay(); err != nil {
		fmt.Printf("Erro ao rodar Overlay Desktop: %v\n", err)
		os.Exit(1)
	}
}
