# Calculadora de Saída

Uma aplicação simples em Python para calcular o horário de saída do trabalho com base na hora de entrada, tempo de almoço e jornada de trabalho.

## Funcionalidades

- Entrada de horário de início no formato `HH:MM`
- Registro do tempo de almoço em minutos
- Definição da jornada de trabalho em horas
- Exibe o horário previsto de saída
- Atualização em tempo real da hora atual e do tempo restante
- Indica quando você está em hora extra
- Marca d'água opcional, transparente e sempre visível sobre outras janelas
- Temas Azul, Verde, Roxo, Âmbar e Claro

## Tecnologias

- Python 3
- customtkinter
- datetime

## Como executar

1. Instale Python 3 caso ainda não tenha.
2. Instale a dependência:

```bash
pip install customtkinter
```

3. Execute o aplicativo:

```bash
python app.py
```

## Builds automáticos

A workflow `Build e Release` do GitHub Actions gera:

- `calculo-ponto-windows-x86_64.exe` para Windows, com ícone de relógio;
- pacote `.deb` para Debian e Ubuntu;
- pacote `.rpm` para Fedora;
- pacote `.pkg.tar.zst` para Arch Linux;
- binário Linux portátil e arquivo `.tar.gz`;
- arquivos SHA-256 para verificação dos downloads.

Ela é executada em pushes para `main`, pull requests e manualmente na aba
**Actions**. Os resultados ficam disponíveis na seção **Artifacts** de cada
execução durante 30 dias.

Cada commit enviado ou mesclado na `main` também cria automaticamente uma tag
incremental no formato `v0.0.N` e publica os arquivos em uma GitHub Release.
Pull requests e execuções manuais apenas geram os artefatos, sem criar tags.

Para gerar localmente o ícone usado pelo PyInstaller:

```bash
python -m pip install Pillow
python scripts/generate_icon.py
```

## Observações

- O aplicativo usa `customtkinter` para interface gráfica.
- A janela tem tamanho fixo de `420x420`.
- Caso os dados de entrada estejam inválidos, a aplicação exibirá "Dados inválidos.".

## Estrutura do projeto

- `app.py` - código principal da aplicação
- `app.spec` - especificação para empacotamento com PyInstaller
- `build/` - saída de build gerada pelo PyInstaller

## Uso

1. Informe a hora de entrada em `HH:MM`.
2. Informe o tempo de almoço em minutos.
3. Informe a jornada de trabalho em horas.
4. A tela exibirá o horário de saída e o tempo restante.

---

Bom trabalho e feliz cálculo de ponto!
