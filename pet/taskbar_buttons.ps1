# Prints where the taskbar's app icons are, as JSON: {"x", "y", "w", "h", "how"} of the strip that holds them
# (screen pixels). Pixel Fox looks at that strip to find icons to dig at. Nothing is opened, clicked or changed.
# Works on Windows 10 (the classic task list), Windows 11 (the new taskbar frame), and falls back to the whole
# taskbar. Prints {} if there is no taskbar to find.
$ErrorActionPreference = "SilentlyContinue"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
function Cond($property, $value) { New-Object System.Windows.Automation.PropertyCondition($property, $value) }
function Strip($element, $how) {
    # The element's rectangle as JSON, or $null if it's missing or too small to hold icons.
    if (-not $element) { return $null }
    $r = $element.Current.BoundingRectangle
    if ($r.Width -lt 20 -or $r.Height -lt 10) { return $null }
    return ConvertTo-Json -Compress -InputObject ([PSCustomObject]@{ x = [int]$r.X; y = [int]$r.Y; w = [int]$r.Width; h = [int]$r.Height; how = $how })
}
$tray = $A::RootElement.FindFirst($Scope::Children, (Cond $A::ClassNameProperty "Shell_TrayWnd"))
if (-not $tray) { "{}"; exit }
# Windows 10: the running-applications list
$found = Strip $tray.FindFirst($Scope::Descendants, (Cond $A::ClassNameProperty "MSTaskListWClass")) "windows10"
# Windows 11: the XAML taskbar frame that holds the app buttons
if (-not $found) { $found = Strip $tray.FindFirst($Scope::Descendants, (Cond $A::AutomationIdProperty "TaskbarFrame")) "windows11" }
if (-not $found) { $found = Strip $tray.FindFirst($Scope::Descendants, (Cond $A::ClassNameProperty "Taskbar.TaskbarFrameAutomationPeer")) "windows11" }
# Anything else: the whole taskbar (the icon finder ignores things that aren't icon-sized)
if (-not $found) { $found = Strip $tray "taskbar" }
if ($found) { $found } else { "{}" }
