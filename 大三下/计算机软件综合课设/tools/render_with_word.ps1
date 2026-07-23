param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $document = $word.Documents.Open($InputPath, $false, $true)
    foreach ($toc in $document.TablesOfContents) { $toc.Update() | Out-Null }
    $document.Fields.Update() | Out-Null
    $document.ExportAsFixedFormat($OutputPath, 17)
    $document.Close($false)
} finally {
    $word.Quit()
}
