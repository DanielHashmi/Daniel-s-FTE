param(
  [string]$EnvPath = ".env"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-DotEnv {
  param([string]$Path)

  if (-not (Test-Path $Path)) {
    throw "Env file not found: $Path"
  }

  $map = @{}
  foreach ($line in Get-Content $Path) {
    if ($line -match "^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$") {
      $map[$matches[1]] = $matches[2].Trim()
    }
  }
  return $map
}

function Parse-GraphError {
  param($ErrorRecord)

  if ($ErrorRecord.ErrorDetails -and $ErrorRecord.ErrorDetails.Message) {
    try {
      $json = $ErrorRecord.ErrorDetails.Message | ConvertFrom-Json
      if ($json.error) {
        return @{
          code = $json.error.code
          subcode = $json.error.error_subcode
          type = $json.error.type
          message = $json.error.message
        }
      }
    } catch {
      return @{
        code = ""
        subcode = ""
        type = ""
        message = $ErrorRecord.ErrorDetails.Message
      }
    }
  }

  return @{
    code = ""
    subcode = ""
    type = ""
    message = $ErrorRecord.Exception.Message
  }
}

function Invoke-GraphGet {
  param(
    [string]$Uri
  )

  try {
    $data = Invoke-RestMethod -Method Get -Uri $Uri -TimeoutSec 30
    return @{
      ok = $true
      data = $data
      error = $null
    }
  } catch {
    return @{
      ok = $false
      data = $null
      error = Parse-GraphError $_
    }
  }
}

function Print-Result {
  param(
    [string]$Status,
    [string]$Label,
    [string]$Detail
  )

  Write-Output ("{0} {1}: {2}" -f $Status, $Label, $Detail)
}

$envMap = Read-DotEnv -Path $EnvPath
$version = if ($envMap["META_GRAPH_API_VERSION"]) { $envMap["META_GRAPH_API_VERSION"] } else { "v19.0" }

$fbMethod = $envMap["FACEBOOK_POST_METHOD"]
$igMethod = $envMap["INSTAGRAM_POST_METHOD"]
$fbPageId = $envMap["FACEBOOK_PAGE_ID"]
$fbPageToken = $envMap["FACEBOOK_PAGE_TOKEN"]
$igId = $envMap["INSTAGRAM_BUSINESS_ID"]
$igToken = $envMap["INSTAGRAM_ACCESS_TOKEN"]

$hasFailure = $false

if ($fbMethod -ne "graph_api") {
  Print-Result -Status "WARN" -Label "facebook_method" -Detail ("Expected graph_api, found '{0}'" -f $fbMethod)
}
if ($igMethod -ne "graph_api") {
  Print-Result -Status "WARN" -Label "instagram_method" -Detail ("Expected graph_api, found '{0}'" -f $igMethod)
}

if (-not $fbPageId -or -not $fbPageToken) {
  Print-Result -Status "FAIL" -Label "facebook_config" -Detail "FACEBOOK_PAGE_ID or FACEBOOK_PAGE_TOKEN missing"
  $hasFailure = $true
} else {
  $fbBasicUri = "https://graph.facebook.com/{0}/{1}?fields=id,name&access_token={2}" -f $version, $fbPageId, $fbPageToken
  $fbBasic = Invoke-GraphGet -Uri $fbBasicUri
  if ($fbBasic.ok) {
    Print-Result -Status "PASS" -Label "facebook_page_basic" -Detail ("id={0} name={1}" -f $fbBasic.data.id, $fbBasic.data.name)
  } else {
    $e = $fbBasic.error
    Print-Result -Status "FAIL" -Label "facebook_page_basic" -Detail ("code={0} subcode={1} message={2}" -f $e.code, $e.subcode, $e.message)
    $hasFailure = $true
  }

  $fbIgLinkUri = "https://graph.facebook.com/{0}/{1}?fields=instagram_business_account{{id,username}}&access_token={2}" -f $version, $fbPageId, $fbPageToken
  $fbIgLink = Invoke-GraphGet -Uri $fbIgLinkUri
  $linkedIgId = $null
  $linkedIgUsername = $null
  if ($fbIgLink.ok -and $fbIgLink.data.instagram_business_account -and $fbIgLink.data.instagram_business_account.id) {
    $linkedIgId = $fbIgLink.data.instagram_business_account.id
    $linkedIgUsername = $fbIgLink.data.instagram_business_account.username
    Print-Result -Status "PASS" -Label "facebook_page_ig_link" -Detail ("linked_ig_id={0} username={1}" -f $linkedIgId, $linkedIgUsername)
  } else {
    if ($fbIgLink.ok) {
      Print-Result -Status "WARN" -Label "facebook_page_ig_link" -Detail "No instagram_business_account linked to page"
    } else {
      $e = $fbIgLink.error
      Print-Result -Status "FAIL" -Label "facebook_page_ig_link" -Detail ("code={0} subcode={1} message={2}" -f $e.code, $e.subcode, $e.message)
      $hasFailure = $true
    }
  }

  # Validate configured IG token + IG ID
  if (-not $igId -or -not $igToken) {
    Print-Result -Status "FAIL" -Label "instagram_config" -Detail "INSTAGRAM_BUSINESS_ID or INSTAGRAM_ACCESS_TOKEN missing"
    $hasFailure = $true
  } else {
    $igBasicUri = "https://graph.facebook.com/{0}/{1}?fields=id,username,name,media_count&access_token={2}" -f $version, $igId, $igToken
    $igBasic = Invoke-GraphGet -Uri $igBasicUri
    if ($igBasic.ok) {
      Print-Result -Status "PASS" -Label "instagram_business_basic" -Detail ("id={0} username={1} media_count={2}" -f $igBasic.data.id, $igBasic.data.username, $igBasic.data.media_count)
    } else {
      $e = $igBasic.error
      Print-Result -Status "FAIL" -Label "instagram_business_basic" -Detail ("code={0} subcode={1} message={2}" -f $e.code, $e.subcode, $e.message)
      $hasFailure = $true
    }
  }

  # Diagnostic fallback: check if page token + linked IG works when configured IG creds fail
  if ($linkedIgId) {
    $fallbackIgBasicUri = "https://graph.facebook.com/{0}/{1}?fields=id,username&access_token={2}" -f $version, $linkedIgId, $fbPageToken
    $fallbackIgBasic = Invoke-GraphGet -Uri $fallbackIgBasicUri
    if ($fallbackIgBasic.ok) {
      Print-Result -Status "INFO" -Label "instagram_fallback_probe" -Detail ("Page token works with linked IG id={0} username={1}" -f $fallbackIgBasic.data.id, $fallbackIgBasic.data.username)
    } else {
      $e = $fallbackIgBasic.error
      Print-Result -Status "INFO" -Label "instagram_fallback_probe" -Detail ("Page token probe failed: code={0} subcode={1} message={2}" -f $e.code, $e.subcode, $e.message)
    }

    $publishLimitUri = "https://graph.facebook.com/{0}/{1}/content_publishing_limit?access_token={2}" -f $version, $linkedIgId, $fbPageToken
    $publishLimit = Invoke-GraphGet -Uri $publishLimitUri
    if ($publishLimit.ok) {
      if ($publishLimit.data.data -and $publishLimit.data.data.Count -gt 0) {
        Print-Result -Status "INFO" -Label "instagram_publish_limit_probe" -Detail ("quota_usage={0}" -f $publishLimit.data.data[0].quota_usage)
      } else {
        Print-Result -Status "INFO" -Label "instagram_publish_limit_probe" -Detail "response_ok"
      }
    } else {
      $e = $publishLimit.error
      Print-Result -Status "INFO" -Label "instagram_publish_limit_probe" -Detail ("code={0} subcode={1} message={2}" -f $e.code, $e.subcode, $e.message)
    }
  }
}

if ($hasFailure) {
  Write-Output "OVERALL FAIL"
  exit 1
}

Write-Output "OVERALL PASS"
exit 0
