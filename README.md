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
- Marca d'água arrastável, inclusive entre monitores
- Fonte e tamanho da marca d'água personalizáveis
- Cores independentes para hora atual, saída, tempo restante e hora extra
- Aparência Escura, Clara ou igual à configuração do Windows
- Paletas de destaque Azul, Verde, Roxo e Âmbar
- Preferências salvas automaticamente entre as execuções
- Pode ser ocultada na bandeja do Windows, com opções para abrir ou sair

## Tecnologias

- Python 3
- customtkinter
- datetime

## Como executar

1. Instale Python 3 caso ainda não tenha.
2. Instale a dependência:

```bash
pip install customtkinter Pillow pystray
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
- A janela abre em `460x675` e pode ser redimensionada verticalmente.
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
5. Em **Aparência**, escolha o modo visual e a cor de destaque.
6. Ative a marca d'água e use **Personalizar marca d'água** para escolher
   fonte, tamanho e as cores de cada informação.
7. Para reposicionar a marca d'água, arraste qualquer uma de suas linhas.
8. Use **Ocultar na bandeja do Windows** ou feche a janela pelo “X” para
   mantê-la em segundo plano. Clique duas vezes no ícone da bandeja ou use
   **Abrir** no menu; use **Sair** para encerrar o aplicativo.

---

Bom trabalho e feliz cálculo de ponto!
