# Prints where the taskbar's app icons are, as JSON: {"x", "y", "w", "h"} of the strip that holds them
# (screen pixels). Pixel Fox looks at that strip to find icons to dig at. Nothing is opened, clicked or changed.
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [System.Windows.Automation.AutomationElement]
$byClass = { param($name) New-Object System.Windows.Automation.PropertyCondition($A::ClassNameProperty, $name) }
$tray = $A::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Children, (& $byClass "Shell_TrayWnd"))
$list = if ($tray) { $tray.FindFirst([System.Windows.Automation.TreeScope]::Descendants, (& $byClass "MSTaskListWClass")) }
if (-not $list) { "{}"; exit }
$r = $list.Current.BoundingRectangle
ConvertTo-Json -Compress -InputObject ([PSCustomObject]@{ x = [int]$r.X; y = [int]$r.Y; w = [int]$r.Width; h = [int]$r.Height })
