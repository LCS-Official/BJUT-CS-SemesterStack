$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = (Get-ChildItem -LiteralPath $root -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "exp2_mix.pcapng") } |
    Select-Object -First 1).FullName
if (-not $out) { throw "Cannot find output directory containing exp2_mix.pcapng" }
$pcap = Join-Path $out "exp2_mix.pcapng"
$guiPcap = Join-Path ([System.IO.Path]::GetTempPath()) "exp2_mix_for_wireshark_gui.pcapng"
Copy-Item -LiteralPath $pcap -Destination $guiPcap -Force
$wireshark = Join-Path $root "WiresharkPortable64\App\Wireshark\Wireshark.exe"
$falco = Join-Path $root "WiresharkPortable64\App\Wireshark\plugins\falco"
$falcoOff = Join-Path $root "WiresharkPortable64\App\Wireshark\plugins\falco.disabled_for_screenshots"

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public class NativeWin {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}
"@

function Get-Title($handle) {
    $sb = [System.Text.StringBuilder]::new(512)
    [void][NativeWin]::GetWindowText($handle, $sb, $sb.Capacity)
    $sb.ToString()
}

function Save-Window($handle, $path) {
    if ($handle -eq [IntPtr]::Zero) { throw "Window handle is empty" }
    [NativeWin]::ShowWindow($handle, 3) | Out-Null
    [NativeWin]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Milliseconds 900
    $rect = New-Object NativeWin+RECT
    [NativeWin]::GetWindowRect($handle, [ref]$rect) | Out-Null
    $w = $rect.Right - $rect.Left
    $h = $rect.Bottom - $rect.Top
    $bmp = [System.Drawing.Bitmap]::new($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("wireshark_gui_" + [guid]::NewGuid().ToString("N") + ".png")
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Png)
    Move-Item -LiteralPath $tmp -Destination $path -Force
    $g.Dispose()
    $bmp.Dispose()
}

function Quote-Arg($s) {
    if ($s -match '[\s"]') { '"' + $s.Replace('"', '\"') + '"' } else { $s }
}

function Shot {
    param(
        [string]$name,
        [string[]]$wsArgs,
        [bool]$activeDialog = $false
    )
    $argLine = ($wsArgs | ForEach-Object { Quote-Arg $_ }) -join " "
    $p = Start-Process -FilePath $wireshark -ArgumentList $argLine -PassThru
    try {
        $deadline = (Get-Date).AddSeconds(18)
        while ($p.MainWindowHandle -eq 0 -and (Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 300
            $p.Refresh()
        }
        Start-Sleep -Seconds 4
        $handle = $p.MainWindowHandle
        if ($activeDialog) {
            $fg = [NativeWin]::GetForegroundWindow()
            $title = Get-Title $fg
            if ($title) { $handle = $fg }
        }
        Save-Window $handle (Join-Path $out $name)
    }
    finally {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
    }
}

function ShotProtocolHierarchy($name) {
    $argLine = (@("-r", $guiPcap) | ForEach-Object { Quote-Arg $_ }) -join " "
    $p = Start-Process -FilePath $wireshark -ArgumentList $argLine -PassThru
    try {
        $deadline = (Get-Date).AddSeconds(18)
        while ($p.MainWindowHandle -eq 0 -and (Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 300
            $p.Refresh()
        }
        Start-Sleep -Seconds 4
        [NativeWin]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
        [NativeWin]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
        Start-Sleep -Milliseconds 700
        $shell = New-Object -ComObject WScript.Shell
        $shell.SendKeys("%s")
        Start-Sleep -Milliseconds 400
        $shell.SendKeys("p")
        Start-Sleep -Seconds 3
        $handle = [NativeWin]::GetForegroundWindow()
        if ($handle -eq [IntPtr]::Zero) { $handle = $p.MainWindowHandle }
        Save-Window $handle (Join-Path $out $name)
    }
    finally {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 800
    }
}

$renamedFalco = $false
if ((Test-Path -LiteralPath $falco) -and -not (Test-Path -LiteralPath $falcoOff)) {
    Move-Item -LiteralPath $falco -Destination $falcoOff
    $renamedFalco = $true
}

try {
    Shot -name "wireshark_gui_01_overview.png" -wsArgs @("-r", $guiPcap)
    Shot -name "wireshark_gui_02_icmp_filter.png" -wsArgs @("-r", $guiPcap, "-Y", "icmp", "-g", "13")
    Shot -name "wireshark_gui_03_arp_filter.png" -wsArgs @("-r", $guiPcap, "-Y", "arp", "-g", "21")
    Shot -name "wireshark_gui_04_tcp_ipv4_filter.png" -wsArgs @("-r", $guiPcap, "-Y", "tcp and ip", "-g", "24")
    Shot -name "wireshark_gui_05_udp_dns_filter.png" -wsArgs @("-r", $guiPcap, "-Y", "dns or udp", "-g", "80")
    ShotProtocolHierarchy "wireshark_gui_06_protocol_hierarchy.png"
}
finally {
    if ($renamedFalco -and (Test-Path -LiteralPath $falcoOff) -and -not (Test-Path -LiteralPath $falco)) {
        Move-Item -LiteralPath $falcoOff -Destination $falco
    }
}
