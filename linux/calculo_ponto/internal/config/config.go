package config

import (
	"encoding/json"
	"os"
	"path/filepath"

	"calculo_ponto/internal/calculator"
)

func getConfigFilePath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "ponto_config.json", nil
	}
	dir := filepath.Join(home, ".config", "ponto")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "ponto_config.json", nil
	}
	return filepath.Join(dir, "config.json"), nil
}

// Load carrega a configuração salva em disco ou retorna o padrão.
func Load() calculator.ShiftConfig {
	def := calculator.DefaultConfig()

	path, err := getConfigFilePath()
	if err != nil {
		return def
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return def
	}

	cfg := def
	if err := json.Unmarshal(data, &cfg); err != nil {
		return def
	}

	if cfg.Theme == "" {
		cfg.Theme = def.Theme
	}

	return cfg
}

// Save salva a configuração atual em disco.
func Save(cfg calculator.ShiftConfig) error {
	path, err := getConfigFilePath()
	if err != nil {
		return err
	}

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, data, 0644)
}
