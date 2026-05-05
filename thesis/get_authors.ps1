
$dois = @(
  "10.1109/ACCESS.2024.3409057",
  "10.1007/s10766-021-00712-3",
  "10.48550/arXiv.2304.10020",
  "10.3390/app122010619",
  "10.1145/3576841.3589626",
  "10.1109/TSC.2021.3098816",
  "10.1109/LCN52139.2021.9524928",
  "10.48550/arXiv.2411.16086",
  "10.1145/3410338.3412338",
  "10.48550/arXiv.2601.08025"
)
foreach ($doi in $dois) {
  try {
    $res = Invoke-RestMethod "https://api.crossref.org/works/$doi" -ErrorAction Stop
    $authors = $res.message.author | ForEach-Object { "$($_.family), $($_.given)" }
    Write-Host "$doi -> $($authors -join " and ")"
  } catch {
    Write-Host "$doi -> NOT FOUND"
  }
}