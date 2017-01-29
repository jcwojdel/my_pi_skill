#!/bin/bash
SECRET=PLACE_HERE_A_SECRET
DATE=`date '+%Y%m%d'`
SEEDED_SECRET=`echo -n "$DATE$SECRET" | md5sum | awk '{print $1}'`

echo "Setting kodi web password to: "$SEEDED_SECRET

if [[ "x$1" == "x" ]] ; then
  systemctl stop kodi
fi

sed 's/<webserverpassword>.*<\/webserverpassword>/<webserverpassword>'$SEEDED_SECRET'<\/webserverpassword>/' /storage/.kodi/userdata/guisettings.xml > /storage/guisettings.tmp
mv /storage/guisettings.tmp /storage/.kodi/userdata/guisettings.xml

if [[ "x$1" == "x" ]] ; then
  systemctl start kodi
fi
