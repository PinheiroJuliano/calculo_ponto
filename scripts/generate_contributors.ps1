param(
    [string]$OutputPath = "AUTHORS.txt"
)

$ErrorActionPreference = "Stop"

$contributors = @(
    git log --use-mailmap --format="%aN <%aE>" HEAD |
        Sort-Object -Unique
)
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel consultar os contribuidores no historico Git."
}

$lines = @(
    "Calculadora de Saida"
    ""
    "Projeto mantido por PisJuliano e construido com as contribuicoes de:"
    ""
)
$lines += $contributors | ForEach-Object { "- $_" }
$lines += @(
    ""
    "Esta lista e gerada a partir dos autores de commits do repositorio."
)

$absolutePath = [System.IO.Path]::GetFullPath($OutputPath)
$directory = [System.IO.Path]::GetDirectoryName($absolutePath)
if ($directory) {
    [System.IO.Directory]::CreateDirectory($directory) | Out-Null
}
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllLines($absolutePath, $lines, $utf8WithoutBom)
