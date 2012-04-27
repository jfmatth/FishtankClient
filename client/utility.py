import os
import platform
import ctypes

def get_free_space(folder):
    """ Return folder/drive free space (in bytes)
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        return os.statvfs(folder).f_bfree
        
def validate_settings(settings = None):
    # validate all settings in a settings session

    def check_dir(path=None):
        
        if path == None:
            raise Exception("Can't check a blank path")
            
        if not os.path.exists(path):
            os.mkdir(path)
    
    if settings == None:
        raise Exception("No settings variable specified")

    # if there is a .guid entry, then we are registered, otherwise, not.
    if not settings['.guid'] == None:
#        if settings["block_sz"] == None:
#            raise Exception("setting block_sz missing")
        if settings["filespec"] == None:
            raise Exception("setting filespec missing")
        if settings["temppath"] == None:
            raise Exception("setting temppath missing")
        if settings["dbpath"] == None:
            raise Exception("setting dbpath missing")
        if settings[".publickey"] == None:
            raise Exception("setting .publickey missing")
        if settings["cloud_files"] == None:
            raise Exception("setting cloud_files missing")
        if settings["cloud_meta"] == None:
            raise Exception("setting cloud_meta missing")
        if settings["tracker_ip"] == None:
            raise Exception("setting tracker_ip missing")
        if settings["max_free_perc"] == None:
            raise Exception("max_free_perc missing")
        if settings["min_free_gb"] == None:
            raise Exception("min_free_gb missing")
        if settings["backupsize"] == None:
            raise Exception("backupsize missing")
        
        if settings['.installdir'] == None:
            raise Exception(".installdir missing")
        
        # check our directories, create them if they don't exist.
        insdir = settings['.installdir']
        check_dir(os.path.normpath(settings["temppath"]) )
        check_dir(os.path.normpath(insdir + settings["dbpath"]) )
        check_dir(os.path.normpath(insdir + settings["cloud_files"]) )
        check_dir(os.path.normpath(insdir + settings["cloud_meta"]) )
        
        # check log_path setup, only if it exists.
        if not settings["log_path"] == None:
            check_dir(os.path.normpath(insdir + settings["log_path"]) )
        
