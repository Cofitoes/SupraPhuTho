Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Popup "Hệ thống tự động đồng bộ (1 phút/lần) đã được khởi động và đang chạy ngầm!", 3, "Supra Auto Sync", 64
WshShell.Run chr(34) & currentDir & "\Cap_Nhat_Du_Lieu_Auto.bat" & chr(34), 0
Set WshShell = Nothing
