import os, time
p = '/app/data/scanner_heartbeat'
if os.path.exists(p):
    age = int(time.time() - os.path.getmtime(p))
    print(f'Heartbeat age: {age}s')
    if age > 120:
        print(f'WARNING: Heartbeat is STALE ({age}s > 120s) — scanner loop may be hung')
    else:
        print('OK: Heartbeat fresh — scanner loop is alive')
else:
    print('NOT FOUND: /app/data/scanner_heartbeat does not exist inside container')
    print('Scanner has not completed its first cycle yet, or _touch_heartbeat() is failing silently')
