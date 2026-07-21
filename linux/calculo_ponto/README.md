# Calculadora de Ponto & Cronômetro Overlay Sowon em Go

Uma aplicação moderna desenvolvida em **Golang** que combina um **Painel Interativo de Configuração de Ponto no Terminal (TUI)** com um **Cronômetro Overlay Flutuante (Always-On-Top e Transparente) estilo Sowon**.

## Como Funciona

Ao executar `./ponto`:
1. **No seu Terminal:** Abre o **Painel Interativo TUI** onde você pode visualizar os resultados e editar a Hora de Entrada, Almoço e Jornada.
2. **Na sua Tela (Desktop Overlay):** Abre um **widget flutuante Always-On-Top** no canto superior direito da tela com o **Cronômetro Sowon** em dígitos digitais 7-segmentos.
3. **Sincronização em Tempo Real:** Qualquer alteração feita e salva na TUI no terminal atualiza o Cronômetro Overlay flutuante instantaneamente em tempo real!

---

## Modos e Atalhos (Executados no Terminal)

Como o Overlay flutuante possui *Mouse Passthrough* (os cliques do mouse passam direto para as suas janelas de trabalho), o controle do cronômetro é feito diretamente no seu **Terminal**:

- **`<F1>` / `<1>`**: Modo Contagem Regressiva (Tempo até a saída)
- **`<F2>` / `<2>`**: Modo Tempo Trabalhado (Stopwatch)
- **`<F3>` / `<3>`**: Modo Relógio em Tempo Real
- **`<F5>` / `<R>`**: Reiniciar o cronômetro Sowon
- **`<F6>` / `<C>`**: Alternar o canto do monitor (Canto Superior Direito -> Inferior Direito -> Inferior Esquerdo -> Superior Esquerdo)
- **`<F7>` / `<T>`**: Alternar Tema de Cores do Overlay (Cyan -> Matrix Green -> Cyberpunk Pink -> Amber Gold -> Minimal White)
- **`<F8>` / `<O>`**: Alternar Opacidade do Fundo (Transparente 0% -> 40% -> 75% -> 95%)
- **`<F9>` / `<B>`**: Alternar Exibição da Borda do Widget (Ligada / Desligada)
- **`<TAB>` / `<Shift+TAB>`**: Navegar pelos campos de texto e botão Salvar
- **`<ENTER>`**: Salvar parâmetros de horários e atualizar o Overlay em tempo real
- **`<ESC>` / `<Q>`**: Sair da aplicação

---

## Como Executar e Compilar

### Executar diretamente

```bash
go run main.go
```

### Compilar binário standalone

```bash
go build -o ponto main.go
./ponto
```

### Alterar horários via flags rápidas

```bash
./ponto --entrada 08:30 --almoco 45 --jornada 8.5
```

---

Bom trabalho e feliz cálculo de ponto!