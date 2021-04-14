from ftplib import FTP
import os

ftp_host = 'ftp.gridpointweather.com'
ftp_acct = 'wefs'
ftp_pass = 'conED#18'


def grabFile(filename,ftp,directory):
    localfile = open(directory+'/'+filename, 'wb')
    ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
    localfile.close()
    
def ftp_fetch():
    files = []
    with FTP(ftp_host) as ftp:
        ftp.login(ftp_acct, ftp_pass) # connect to host, default port
        dirs = ftp.nlst()
        ftp.cwd(dirs[0])
        for d in dirs:
            directory = 'netcdf/'+d
            if not os.path.exists(directory):os.makedirs(directory)
            ftp.cwd('../'+d)
        #     ls = []
        #     ftp.retrlines('LIST', ls.append)
        #     for entry in ls:
        #         print('e',entry)
            files=ftp.nlst()
            for f in files: grabFile(f,ftp,directory)
        ftp.quit()

if __name__ == '__main__':
    ftp_fetch()
    

    # print(files)