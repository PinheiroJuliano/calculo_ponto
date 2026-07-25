param(
    [Parameter(Mandatory = $true)]
    [string]$AppVersion,
    [string]$OutputPath = "packaging/windows/version_info.txt"
)

$ErrorActionPreference = "Stop"

$numbers = @($AppVersion.Split(".") | ForEach-Object {
    if ($_ -notmatch "^\d+$") {
        throw "A versao deve conter somente numeros separados por pontos."
    }
    [int]$_
})
if ($numbers.Count -gt 4) {
    throw "A versao do Windows pode ter no maximo quatro componentes."
}
while ($numbers.Count -lt 4) {
    $numbers += 0
}
$tuple = $numbers -join ", "

$content = @"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($tuple),
    prodvers=($tuple),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '041604B0',
        [
          StringStruct('CompanyName', 'PisJuliano e contribuidores'),
          StringStruct('FileDescription', 'Calculadora de Saida'),
          StringStruct('FileVersion', '$AppVersion'),
          StringStruct('InternalName', 'calculo-ponto'),
          StringStruct('LegalCopyright', 'Copyright (c) PisJuliano e contribuidores'),
          StringStruct('OriginalFilename', 'calculo-ponto.exe'),
          StringStruct('ProductName', 'Calculadora de Saida'),
          StringStruct('ProductVersion', '$AppVersion')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
"@

$absolutePath = [System.IO.Path]::GetFullPath($OutputPath)
$directory = [System.IO.Path]::GetDirectoryName($absolutePath)
[System.IO.Directory]::CreateDirectory($directory) | Out-Null
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($absolutePath, $content, $utf8WithoutBom)
