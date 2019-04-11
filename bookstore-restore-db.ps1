#
# Восстанавливает базу данных учебного проекта.
#
$BackUpFilePath = "D:\DB\BookStore.bak"
$FileNumber = 1
$DataBase = "BookStore"

$ScriptPath = Join-Path -Path (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent) -ChildPath "Common\restore-any-db.ps1"

& $ScriptPath -Database $DataBase -BackUpFilePath $BackUpFilePath -FileNumber $FileNumber
    
