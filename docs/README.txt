To automatically recompile docs when the sources change, use `entr`[*]:
  ls -d * */* | grep -v _build | entr -n make html

[*] http://eradman.com/entrproject/
