import win32com.client
import active_directory

session = win32com.client.gencache.EnsureDispatch("MAPI.session")
win32com.client.gencache.EnsureDispatch("Outlook.Application")
outlook = win32com.client.Dispatch("Outlook.Application")
mapi = outlook.GetNamespace('MAPI')
inbox =  mapi.GetDefaultFolder(win32com.client.constants.olFolderInbox)

fldr_iterator = inbox.Folders
desired_folder = None
while 1:
    f = fldr_iterator.GetNext()
    if not f: break
    if f.Name == 'test':
        print 'found "test" dir'
        desired_folder = f
        break

print desired_folder.Name