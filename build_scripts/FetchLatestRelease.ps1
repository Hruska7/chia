
param (
  [Parameter(Mandatory=$true)]
  [Alias("u")]
  [String]$releaseUrl,

  [Parameter(Mandatory=$true)]
  [Alias("p")]
  [String[]]$patterns,

  [Parameter(Mandatory=$true)]
  [Alias("o")]
  [String[]]$outputs
)

# Make a GET request to the API endpoint and parse the response as JSON
$response = Invoke-RestMethod -Uri $releaseUrl

# Extract the version number from the response and output it
$version = $response.tag_name
Write-Output "The latest version is $version for release $releaseUrl"

# Fetch each requested package identified by its pattern and download it
for ($i = 0; $i -lt $patterns.Length; $i++) {
  $pattern = $patterns[$i]
  $output = $outputs[$i]

  $packageUrl = ($response.assets | Where-Object { $_.browser_download_url -like "*/$version/$pattern" }).browser_download_url
  Write-Output "Download url is $packageUrl"

  # Download the package and output to the specified filename
  Invoke-WebRequest -Uri $packageUrl -OutFile "$output"
}

