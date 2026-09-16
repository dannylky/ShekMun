# cam-default.ps1 - resets all room cameras to their default position.
# Called silently by the "Cam default" button in monitor-control.
# Each URL presses the location preset on the room's AVProc (Companion).

$urls = @(
    'http://172.18.2.51:8000/api/location/1/2/4/press',   # SM01 Cam1
    'http://172.18.2.52:8000/api/location/1/0/4/press',   # SM02
    'http://172.18.2.53:8000/api/location/1/0/4/press',   # SM03
    'http://172.18.2.54:8000/api/location/1/0/4/press',   # SM04
    'http://172.18.2.55:8000/api/location/1/0/4/press',   # SM05
    'http://172.18.2.56:8000/api/location/1/0/4/press',   # SM06
    'http://172.18.2.57:8000/api/location/1/0/4/press',   # SM07
    'http://172.18.2.58:8000/api/location/1/0/4/press'    # SM08
)

foreach ($u in $urls) {
    try {
        Invoke-RestMethod -Uri $u -Method Post -TimeoutSec 5 | Out-Null
    } catch {
        # silent - a room may be offline
    }
}