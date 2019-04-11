<#
    Функция ожидания нажатия клавиши.
#>
function WaitAKey
{
    param(
	   # Флаг - останавливаться и ожидать нажатия клавиши.
       [parameter(Mandatory=$true)]
       [switch] $Pause
    )


    if (-not $psISE -and $Pause)
    {
        Write-Host('Нажмите любую клавишу ...')
        $x = $host.UI.RawUI.ReadKey("NoEcho, IncludeKeyDown")
    }
}

$CcollabPath = "C:\Program Files\Collaborator Client\ccollab.exe"

