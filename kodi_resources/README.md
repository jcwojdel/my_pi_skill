Place the file on Kodi distribution, somewhere on persistant storage, e.g.:

```
  /storage/.kodi/bin/reset_password.sh
```

Then make sure it is run on a daily basis via cron. Crontab might look like:

```
  0 0 * * * /storage/.kodi/bin/reset_password.sh > /storage/reset_password.log
```

Finally, add it to the autostart file in `/storage/.config/autostart.sh`:

```
/storage/.kodi/bin-jcw/reset_password.sh NORESTART
```
