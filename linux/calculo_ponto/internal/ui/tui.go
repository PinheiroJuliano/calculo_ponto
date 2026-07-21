package ui

import (
	"fmt"
	"math"
	"strconv"
	"time"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"calculo_ponto/internal/calculator"
	"calculo_ponto/internal/config"
	"calculo_ponto/internal/state"
	"calculo_ponto/internal/timer"
)

type tickMsg time.Time

func tickCmd() tea.Cmd {
	return tea.Tick(1*time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

type Model struct {
	cfg         calculator.ShiftConfig
	inputs      []textinput.Model
	focusIndex  int
	shiftResult calculator.ShiftResult
	calcErr     error
	statusMsg   string
	width       int
	height      int
	appState    *state.AppState
}

func InitialModel() Model {
	cfg := config.Load()

	inputs := make([]textinput.Model, 3)

	// Campo 0: Hora Entrada
	inputs[0] = textinput.New()
	inputs[0].Placeholder = "08:00"
	inputs[0].SetValue(cfg.Entrada)
	inputs[0].CharLimit = 5
	inputs[0].Width = 10
	inputs[0].Focus()

	// Campo 1: Tempo Almoço
	inputs[1] = textinput.New()
	inputs[1].Placeholder = "60"
	inputs[1].SetValue(strconv.Itoa(cfg.Almoco))
	inputs[1].CharLimit = 4
	inputs[1].Width = 10

	// Campo 2: Jornada
	inputs[2] = textinput.New()
	inputs[2].Placeholder = "8.0"
	inputs[2].SetValue(fmt.Sprintf("%.1f", cfg.Jornada))
	inputs[2].CharLimit = 4
	inputs[2].Width = 10

	res, err := calculator.Calculate(cfg, time.Now())
	st := state.GetState()

	return Model{
		cfg:         cfg,
		inputs:      inputs,
		focusIndex:  0,
		shiftResult: res,
		calcErr:     err,
		appState:    st,
		statusMsg:   "Pressione TAB para trocar de campos | ENTER para Salvar | F5: Reset | F6/C: Mover Canto | ESPAÇO: Pausar",
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(
		textinput.Blink,
		tickCmd(),
	)
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {

	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height

	case tickMsg:
		res, err := calculator.Calculate(m.cfg, time.Time(msg))
		m.shiftResult = res
		m.calcErr = err
		cmds = append(cmds, tickCmd())

	case tea.KeyMsg:
		keyStr := msg.String()

		// Atalhos Globais no Terminal
		switch keyStr {

		case "ctrl+c", "esc":
			return m, tea.Quit

		case "f1":
			m.statusMsg = m.appState.SetMode(timer.ModeCountdown)
		case "f2":
			m.statusMsg = m.appState.SetMode(timer.ModeStopwatch)
		case "f3":
			m.statusMsg = m.appState.SetMode(timer.ModeClock)
		case "f5":
			m.statusMsg = m.appState.ResetTimer()
		case "f6":
			m.statusMsg = m.appState.CycleCorner()
		case "f7":
			m.cycleTheme()
		case "f8":
			m.cycleOpacity()
		case "f9":
			m.toggleBorder()

		case "tab":
			m.focusIndex = (m.focusIndex + 1) % 4
			for i := 0; i < len(m.inputs); i++ {
				if i == m.focusIndex {
					m.inputs[i].Focus()
				} else {
					m.inputs[i].Blur()
				}
			}

		case "shift+tab":
			m.focusIndex = (m.focusIndex - 1 + 4) % 4
			for i := 0; i < len(m.inputs); i++ {
				if i == m.focusIndex {
					m.inputs[i].Focus()
				} else {
					m.inputs[i].Blur()
				}
			}

		case "enter", "ctrl+s":
			m.recalculateAndSave()

		default:
			// Atalhos de letra/espaço quando o foco está no botão Salvar (focusIndex == 3)
			if m.focusIndex == 3 {
				switch keyStr {
				case " ":
					m.statusMsg = m.appState.TogglePause()
				case "r":
					m.statusMsg = m.appState.ResetTimer()
				case "c":
					m.statusMsg = m.appState.CycleCorner()
				case "t":
					m.cycleTheme()
				case "o":
					m.cycleOpacity()
				case "b":
					m.toggleBorder()
				case "1":
					m.statusMsg = m.appState.SetMode(timer.ModeCountdown)
				case "2":
					m.statusMsg = m.appState.SetMode(timer.ModeStopwatch)
				case "3":
					m.statusMsg = m.appState.SetMode(timer.ModeClock)
				}
			}
		}
	}

	// Atualiza os textinputs se foco estiver nos campos
	if m.focusIndex < len(m.inputs) {
		var cmd tea.Cmd
		m.inputs[m.focusIndex], cmd = m.inputs[m.focusIndex].Update(msg)
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

func (m *Model) cycleTheme() {
	themes := []string{"cyan", "green", "pink", "amber", "white"}
	currIdx := 0
	for i, t := range themes {
		if t == m.cfg.Theme {
			currIdx = i
			break
		}
	}
	nextTheme := themes[(currIdx+1)%len(themes)]
	m.cfg.Theme = nextTheme
	config.Save(m.cfg)
	m.statusMsg = fmt.Sprintf("Tema alterado para: %s", nextTheme)
}

func (m *Model) cycleOpacity() {
	opacities := []float64{0.0, 0.35, 0.70, 0.95}
	currIdx := -1
	for i, o := range opacities {
		if math.Abs(o-m.cfg.Opacity) < 0.05 {
			currIdx = i
			break
		}
	}
	nextOpacity := opacities[(currIdx+1)%len(opacities)]
	m.cfg.Opacity = nextOpacity
	config.Save(m.cfg)
	m.statusMsg = fmt.Sprintf("Opacidade do Fundo: %.0f%%", nextOpacity*100)
}

func (m *Model) toggleBorder() {
	m.cfg.ShowBorder = !m.cfg.ShowBorder
	config.Save(m.cfg)
	status := "Desligada"
	if m.cfg.ShowBorder {
		status = "Ligada"
	}
	m.statusMsg = fmt.Sprintf("Borda do Overlay: %s", status)
}

func (m *Model) recalculateAndSave() {
	entradaStr := m.inputs[0].Value()
	almocoStr := m.inputs[1].Value()
	jornadaStr := m.inputs[2].Value()

	almocoVal, err1 := strconv.Atoi(almocoStr)
	jornadaVal, err2 := strconv.ParseFloat(jornadaStr, 64)

	if err1 != nil || err2 != nil {
		m.statusMsg = "Erro: Valores numéricos inválidos para almoço ou jornada!"
		return
	}

	m.cfg.Entrada = entradaStr
	m.cfg.Almoco = almocoVal
	m.cfg.Jornada = jornadaVal

	res, err := calculator.Calculate(m.cfg, time.Now())
	m.shiftResult = res
	m.calcErr = err

	if err != nil {
		m.statusMsg = fmt.Sprintf("Erro de validação: %v", err)
		return
	}

	if err := config.Save(m.cfg); err != nil {
		m.statusMsg = fmt.Sprintf("Erro ao salvar configuração: %v", err)
	} else {
		m.statusMsg = "Configurações salvas! O Overlay Flutuante atualizou automaticamente."
	}
}

// View renderiza a interface interativa do terminal.
func (m Model) View() string {
	titleStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#7D56F4")).
		Background(lipgloss.Color("#1E1E2E")).
		Padding(0, 1)

	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7D56F4")).
		Padding(1, 2)

	alertStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#FF453A"))

	successStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("#30D158"))

	statusStyle := lipgloss.NewStyle().
		Foreground(lipgloss.Color("#A1A1A6")).
		Italic(true)

	// Formulário
	var fields string
	fields += fmt.Sprintf("Hora de Entrada (HH:MM):  %s\n", m.inputs[0].View())
	fields += fmt.Sprintf("Almoço (Minutos):         %s\n", m.inputs[1].View())
	fields += fmt.Sprintf("Jornada (Horas):          %s\n\n", m.inputs[2].View())

	btnSave := "[ Salvar e Atualizar Overlay (ENTER) ]"
	if m.focusIndex == 3 {
		btnSave = lipgloss.NewStyle().Background(lipgloss.Color("#30D158")).Foreground(lipgloss.Color("#000000")).Bold(true).Render(btnSave)
	}
	fields += btnSave

	// Resultado
	var calcStatus string
	if m.calcErr != nil {
		calcStatus = alertStyle.Render(fmt.Sprintf("Dados inválidos: %v", m.calcErr))
	} else {
		agoraStr := time.Now().Format("15:04:05")
		saidaStr := m.shiftResult.SaidaPrevista.Format("15:04")
		restanteStr := calculator.FormatDuration(m.shiftResult.Restante)

		calcStatus += fmt.Sprintf("Hora Atual:       %s\n", agoraStr)
		calcStatus += fmt.Sprintf("Saída Prevista:   %s\n\n", lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#00E5FF")).Render(saidaStr))

		if m.shiftResult.IsHoraExtra {
			calcStatus += alertStyle.Render(fmt.Sprintf("HORA EXTRA:       + %s\n\n", restanteStr))
		} else {
			calcStatus += successStyle.Render(fmt.Sprintf("FALTAM:           %s\n\n", restanteStr))
		}

		bStatus := "Sim"
		if !m.cfg.ShowBorder {
			bStatus = "Não"
		}
		calcStatus += fmt.Sprintf("Tema Ativo: %s | Opacidade: %.0f%% | Borda: %s", m.cfg.Theme, m.cfg.Opacity*100, bStatus)
	}

	leftTitle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#7D56F4")).Render("Parâmetros do Ponto")
	rightTitle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#7D56F4")).Render("Resultado & Aparência Overlay")

	leftBox := boxStyle.Render(leftTitle + "\n\n" + fields)
	rightBox := boxStyle.Render(rightTitle + "\n\n" + calcStatus)

	content := lipgloss.JoinHorizontal(lipgloss.Top, leftBox, "  ", rightBox)

	controlsHelp := lipgloss.NewStyle().Foreground(lipgloss.Color("#FFD60A")).Render(
		"Controles do Overlay via Terminal:\n" +
			"• [F1/1] Regressiva | [F2/2] Tempo Trabalhado | [F3/3] Relógio\n" +
			"• [F5/R] Reiniciar  | [F6/C] Alternar Canto   | [ESPAÇO] Pausar\n" +
			"• [F7/T] Trocar Tema| [F8/O] Opacidade Fundo  | [F9/B] Alternar Borda",
	)

	header := titleStyle.Render("CALCULADORA DE PONTO & CONTROLE DE OVERLAY")
	footer := statusStyle.Render(m.statusMsg)

	return lipgloss.JoinVertical(lipgloss.Left,
		header,
		"",
		content,
		"",
		controlsHelp,
		"",
		footer,
	)
}
