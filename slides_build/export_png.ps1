param(
  [string]$Pptx = "D:\tailieuhoctap\Nam4Ky2\foundation_intern\Source\legal_rag_local\slides_build\Legal_RAG_Presentation.pptx",
  [string]$OutDir = "D:\tailieuhoctap\Nam4Ky2\foundation_intern\Source\legal_rag_local\slides_build\preview"
)

if (-not (Test-Path $OutDir)) {
  New-Item -ItemType Directory -Path $OutDir | Out-Null
}
Get-ChildItem -Path $OutDir -Filter "slide-*.png" -ErrorAction SilentlyContinue | Remove-Item -Force

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoTrue
try {
  $pres = $ppt.Presentations.Open($Pptx, $false, $false, $false)
  $width  = 1600
  $height = 900
  for ($i = 1; $i -le $pres.Slides.Count; $i++) {
    $slide = $pres.Slides.Item($i)
    $name  = "slide-{0:D2}.png" -f $i
    $path  = Join-Path $OutDir $name
    $slide.Export($path, "PNG", $width, $height) | Out-Null
    Write-Output $path
  }
  $pres.Close()
} finally {
  $ppt.Quit() | Out-Null
}
