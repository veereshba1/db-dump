if [ ! -d "/mnt/db-backups" ]; then
mkdir /mnt/db-backups
fi
if [ ! -d "/etc/smbcredentials" ]; then
mkdir /etc/smbcredentials
fi
if [ ! -f "/etc/smbcredentials/backups.cred" ]; then
    bash -c 'echo "username=username_goes_here" >> /etc/smbcredentials/backups.cred'
    bash -c 'echo "password=${SMB_PASSWORD}" >> /etc/smbcredentials/backups.cred'
fi
chmod 600 /etc/smbcredentials/backups.cred

# sudo bash -c 'echo "//backups.file.core.windows.net/db-backups/${ENV} /mnt/db-backups cifs nofail,credentials=/etc/smbcredentials/backups.cred,dir_mode=0777,file_mode=0777,serverino,nosharesock,actimeo=30" >> /etc/fstab'
mount -t cifs //backups.file.core.windows.net/db-backups/${ENV} /mnt/db-backups -o credentials=/etc/smbcredentials/backups.cred,dir_mode=0777,file_mode=0777,serverino,nosharesock,actimeo=30
