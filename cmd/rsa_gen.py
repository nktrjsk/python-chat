import asymencrypt as ae
import time

start = time.time()

ae.prkey_export("private", 1024)

end = time.time() - start

print(end)