## Quectel firmware and tools

we try to update quectel to the latest recommended version. The initial need arose with AT&T 3G shutdown.

### Enable/Disable upgrade Feature

All potentially dangerous operations are protected by UPDATE_QUECTEL_EG25G_MODEM. This has to be defined for anything to happen.

### Flashing

Quectel provides a tool named QFirehose to flash the modem. The tool is available in QFirehose directory.
eg.
```
# it is mandatory to stop modem manager before running this command
QFirehose -f <firmware_dir>
```
The process takes about 45 seconds to fully flash. Don't interrupt the process. Modem will most likely be bricked.

Quectel provides them in the form of zip archive. We have hosted it on our GCP server for independent access.

### Testing AT settings.

The modem might be the only connection option on the device. We can't take it from ModemManager. It is better to run them through modem manager dbus interface itself.

eg.
For checking AT&T recommended settings to force 4G LTE connectivity as documented [here](https://docs.sixfab.com/page/att-3g-sunset-guide).
```
# Read ue setting
mmcli -m 0 --command='AT+QNVFR="/nv/item_files/modem/mmode/ue_usage_setting"'

# Set modem to data cetric by writing ue setting. This alone should be able to fix the 3g shutdown issue.
# It is better to set the service domain to Packet Switched as well as shown next.
mmcli -m 0 --command='AT+QNVFW="/nv/item_files/modem/mmode/ue_usage_setting",01'

# Read domain setting
mmcli -m 0 --command='AT+QCFG="servicedomain"'

# Set domain to PS(packet switched) only.
mmcli -m 0 --command='AT+QCFG="servicedomain",1,1'

# Read full firmware version
mmcli -m 0 --command='AT+QGMR'

# Reset modem
mmcli -m 0 --command='AT+CFUN=1,1'
```
For more information about at commands for the module in use, refer Quectel documentation.

### Process flow. What and why of it.

We take two pronged approach to have maximum chances of success.
All operations have capability to rollback if connectivity is lost after making the change.
Look at [quectel.py](../hw_diag/utilities/quectel.py) for more information.:

* First we set the modem settings: UE data centric and servicedomain to PS only as recommended [here](https://docs.sixfab.com/page/att-3g-sunset-guide).

* Then we check the current firmware version and update it if needed. This can potentially give trouble with some providers like T-Mobile. By default T-Mobile is configured to have ipv6 only connectivity in version EG25GGBR07A07M2G_30.003.30.003. For this reason, initially we have restricted the firmware upgrade to AT&T sim holders. In any case, we download firmware at first opportunity for any future need eg if the user installs a new AT&T sim in the field.

The task is configured to runs 2 minutes after app scheduler starts and every hour after that. But future runs will not do anything if the modem is already in desired state.
