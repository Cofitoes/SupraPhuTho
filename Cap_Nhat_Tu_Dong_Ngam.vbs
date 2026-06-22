Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & currentDir & "\Cap_Nhat_Du_Lieu_Auto.bat" & chr(34), 0
Set WshShell = Nothing
