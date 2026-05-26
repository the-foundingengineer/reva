import sys
import traceback

try:
    import app.main
    with open('tb.log', 'w') as f:
        f.write("Success!")
except Exception:
    with open('tb.log', 'w') as f:
        traceback.print_exc(file=f)
