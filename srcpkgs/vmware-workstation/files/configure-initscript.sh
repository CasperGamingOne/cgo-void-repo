#!/bin/sh
# Helper for VMware installer service on Void Linux (runit)

action="$1"
serviceName="$2"

case "$action" in
   add|remove)
      exit 0
      ;;
   status)
      if [ "$serviceName" = "vmware" ]; then
         exit 5
      fi
      if sv status "$serviceName" >/dev/null 2>&1; then
         echo 'on'
         exit 5
      else
         echo 'off'
         exit 6
      fi
      ;;
   *)
      exit 0
      ;;
esac
