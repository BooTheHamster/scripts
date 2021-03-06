#
# Восстанавливает базу данных
#

Param(
	# Наименование базы данных.
    [parameter(Mandatory=$false)]
    [string] $ServerInstance = "localhost\SQLEXPRESS",

	# Наименование базы данных.
    [parameter(Mandatory=$true)]
    [string] $Database,
    
	# Полный путь к файлу бекапа базы данных.
    [parameter(Mandatory=$true)]
    [string] $BackUpFilePath,

	# Номер файла
    [parameter(Mandatory=$true)]
    [int] $FileNumber,
    
	# Флаг - останавливаться и ожидать нажатия клавиши после завершения скрипта.
    [alias("pause")]
    [switch] $PauseAfterEnd = $false
)

$CommonIncludePath = Join-Path -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent) -ChildPath "common.ps1"

. $CommonIncludePath

Try
{
    Import-Module SQLPS -DisableNameChecking

    Write-Host([string]::Format("Восстанавливаем базу данных {0} из {1}", $Database, $BackUpFilePath))
    
	$srv = new-object Microsoft.SqlServer.Management.Smo.Server($ServerInstance)

	if ($srv.Databases[$Database] -ne $null)
	{
		$srv.KillAllProcesses($Database)
	}
	
    Restore-SqlDatabase -ServerInstance $ServerInstance -Database $Database -BackupFile $BackUpFilePath -ReplaceDatabase -FileNumber $FileNumber
}
Catch
{
  Write-Host($_.Exception.Message)
  Write-Host($_.Exception.ItemName)
}
Finally
{
    WaitAKey -Pause:$PauseAfterEnd.IsPresent
}

