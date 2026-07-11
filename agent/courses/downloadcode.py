import os, zipfile

WORK = "/home/jovyan/work"
OUT  = f"{WORK}/work_all.zip"

skip_dirs  = {".ipynb_checkpoints", "__pycache__", ".git", ".ipynb_checkpoints"}
skip_files = {os.path.basename(OUT)}          # 🔑 排除压缩包自己

if os.path.exists(OUT):
    os.remove(OUT)                            # 重跑时先删旧包

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(WORK):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if fn in skip_files:
                continue
            full = os.path.join(dirpath, fn)
            if os.path.abspath(full) == os.path.abspath(OUT):   # 双保险
                continue
            z.write(full, os.path.relpath(full, WORK))

n = len(zipfile.ZipFile(OUT).namelist())
print(OUT, round(os.path.getsize(OUT)/1024/1024, 2), "MB /", n, "files")