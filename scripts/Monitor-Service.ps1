[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https?://')]
    [string]$ServiceUrl,

    [string]$ExpectedDnsName,

    [ValidateRange(1, 60000)]
    [int]$LatencyThresholdMs = 500,

    [ValidateRange(1, 365)]
    [int]$TlsExpiryThresholdDays = 30,

    [string]$IncidentApiUrl,

    [ValidateRange(1, 100)]
    [int]$PollCount = 1,

    [ValidateRange(0, 3600)]
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = 'Stop'
$uri = [Uri]$ServiceUrl
$hostName = if ($ExpectedDnsName) { $ExpectedDnsName } else { $uri.DnsSafeHost }
$incidentEndpoint = if ($IncidentApiUrl) {
    $IncidentApiUrl.TrimEnd('/') + '/api/checks'
} else {
    $ServiceUrl.TrimEnd('/') + '/api/checks'
}

function Get-DnsAddresses {
    param([string]$Name)

    if (Get-Command Resolve-DnsName -ErrorAction SilentlyContinue) {
        return @(Resolve-DnsName -Name $Name -Type A -ErrorAction Stop |
            Where-Object { $_.IPAddress } |
            Select-Object -ExpandProperty IPAddress -Unique)
    }

    return @([System.Net.Dns]::GetHostAddresses($Name) |
        ForEach-Object { $_.IPAddressToString } |
        Select-Object -Unique)
}

function Get-TlsDaysRemaining {
    param([Uri]$TargetUri)

    if ($TargetUri.Scheme -ne 'https') {
        return $null
    }

    $port = if ($TargetUri.Port -gt 0) { $TargetUri.Port } else { 443 }
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $client.Connect($TargetUri.DnsSafeHost, $port)
        $stream = [System.Net.Security.SslStream]::new($client.GetStream(), $false)
        try {
            $stream.AuthenticateAsClient($TargetUri.DnsSafeHost)
            $certificate = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
                $stream.RemoteCertificate
            )
            return [Math]::Round(($certificate.NotAfter.ToUniversalTime() - [DateTime]::UtcNow).TotalDays, 2)
        }
        finally {
            $stream.Dispose()
        }
    }
    finally {
        $client.Dispose()
    }
}

function Invoke-ServiceCheck {
    $dnsAddresses = @()
    $statusCode = $null
    $responseMs = $null
    $tlsDaysRemaining = $null
    $diagnostics = [System.Collections.Generic.List[string]]::new()
    $healthy = $true

    try {
        $dnsAddresses = @(Get-DnsAddresses -Name $hostName)
        if ($dnsAddresses.Count -eq 0) {
            throw "DNS resolution returned no addresses for $hostName"
        }
    }
    catch {
        $healthy = $false
        $diagnostics.Add("DNS: $($_.Exception.Message)")
    }

    try {
        $tlsDaysRemaining = Get-TlsDaysRemaining -TargetUri $uri
        if ($null -ne $tlsDaysRemaining -and $tlsDaysRemaining -lt $TlsExpiryThresholdDays) {
            $healthy = $false
            $diagnostics.Add("TLS certificate expires in $tlsDaysRemaining days")
        }
    }
    catch {
        $healthy = $false
        $diagnostics.Add("TLS: $($_.Exception.Message)")
    }

    foreach ($path in @('/healthz', '/readyz')) {
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-WebRequest -Uri ($ServiceUrl.TrimEnd('/') + $path) -Method Get -TimeoutSec 15
            $stopwatch.Stop()
            $statusCode = [int]$response.StatusCode
            $responseMs = [Math]::Round($stopwatch.Elapsed.TotalMilliseconds, 2)
            if ($statusCode -ne 200 -or $responseMs -gt $LatencyThresholdMs) {
                $healthy = $false
                $diagnostics.Add("$path returned $statusCode in $responseMs ms")
            }
        }
        catch {
            $healthy = $false
            $statusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { $null }
            $diagnostics.Add("${path}: $($_.Exception.Message)")
        }
    }

    $summary = if ($diagnostics.Count) { $diagnostics -join '; ' } else { 'All checks passed' }
    $payload = [ordered]@{
        service_name       = 'production-reliability-platform'
        check_type         = 'synthetic-end-to-end'
        target             = $ServiceUrl
        healthy            = $healthy
        status_code        = $statusCode
        response_ms        = $responseMs
        dns_addresses      = @($dnsAddresses)
        tls_days_remaining = $tlsDaysRemaining
        diagnostic_summary = $summary
        observed_at        = [DateTime]::UtcNow.ToString('o')
    }

    $incidentResult = $null
    try {
        $incidentResult = Invoke-RestMethod `
            -Uri $incidentEndpoint `
            -Method Post `
            -ContentType 'application/json' `
            -Body ($payload | ConvertTo-Json -Depth 5) `
            -TimeoutSec 15
    }
    catch {
        $payload.healthy = $false
        $payload.diagnostic_summary = "$summary; incident API: $($_.Exception.Message)"
    }

    $output = [ordered]@{
        monitor  = $payload
        incident = $incidentResult
    }
    $resolvedExitCode = if ($payload.healthy) {
        0
    }
    elseif ($statusCode -ge 500 -or $null -eq $statusCode) {
        2
    }
    else {
        1
    }
    return [PSCustomObject]@{
        Json     = ($output | ConvertTo-Json -Depth 8)
        ExitCode = $resolvedExitCode
    }
}

$exitCode = 0
for ($index = 1; $index -le $PollCount; $index++) {
    $result = Invoke-ServiceCheck
    Write-Output $result.Json
    $exitCode = $result.ExitCode
    if ($index -lt $PollCount) {
        Start-Sleep -Seconds $IntervalSeconds
    }
}

exit $exitCode
