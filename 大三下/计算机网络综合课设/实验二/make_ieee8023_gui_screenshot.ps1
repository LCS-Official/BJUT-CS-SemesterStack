$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = (Get-ChildItem -LiteralPath $root -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "ieee8023_llc_demo.pcap") } |
    Select-Object -First 1).FullName
if (-not $out) { throw "Cannot find ieee8023_llc_demo.pcap" }

$pcap = Join-Path $out "ieee8023_llc_demo.pcap"
$guiPcap = Join-Path ([System.IO.Path]::GetTempPath()) "ieee8023_llc_demo_for_gui.pcap"
Copy-Item -LiteralPath $pcap -Destination $guiPcap -Force
$wireshark = Join-Path $root "WiresharkPortable64\App\Wireshark\Wireshark.exe"
$falco = Join-Path $root "WiresharkPortable64\App\Wireshark\plugins\falco"
$falcoOff = Join-Path $root "WiresharkPortable64\App\Wireshark\plugins\falco.disabled_for_screenshots"

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class NativeWin {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
}
"@

function Save-Window($handle, $path) {
    [NativeWin]::ShowWindow($handle, 3) | Out-Null
    [NativeWin]::SetForegroundWindow($handle) | Out-Null
    Start-Sleep -Milliseconds 900
    $rect = New-Object NativeWin+RECT
    [NativeWin]::GetWindowRect($handle, [ref]$rect) | Out-Null
    $w = $rect.Right - $rect.Left
    $h = $rect.Bottom - $rect.Top
    if ($w -le 0 -or $h -le 0) { throw "Invalid Wireshark window size" }
    $bmp = [System.Drawing.Bitmap]::new($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bmp.Size)
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("ieee8023_gui_" + [guid]::NewGuid().ToString("N") + ".png")
    $bmp.Save($tmp, [System.Drawing.Imaging.ImageFormat]::Png)
    Move-Item -LiteralPath $tmp -Destination $path -Force
    $g.Dispose()
    $bmp.Dispose()
}

function Quote-Arg($s) {
    if ($s -match '[\s"]') { '"' + $s.Replace('"', '\"') + '"' } else { $s }
}

$renamedFalco = $false
if ((Test-Path -LiteralPath $falco) -and -not (Test-Path -LiteralPath $falcoOff)) {
    Move-Item -LiteralPath $falco -Destination $falcoOff
    $renamedFalco = $true
}

try {
    $args = (@("-r", $guiPcap, "-Y", "llc", "-g", "1") | ForEach-Object { Quote-Arg $_ }) -join " "
    $p = Start-Process -FilePath $wireshark -ArgumentList $args -PassThru
    try {
        $deadline = (Get-Date).AddSeconds(18)
        while ($p.MainWindowHandle -eq 0 -and (Get-Date) -lt $deadline) {
            Start-Sleep -Milliseconds 300
            $p.Refresh()
        }
        Start-Sleep -Seconds 4
        Save-Window $p.MainWindowHandle (Join-Path $out "wireshark_gui_07_ieee8023_llc_demo.png")
    }
    finally {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
}
finally {
    if ($renamedFalco -and (Test-Path -LiteralPath $falcoOff) -and -not (Test-Path -LiteralPath $falco)) {
        Move-Item -LiteralPath $falcoOff -Destination $falco
    }
}

