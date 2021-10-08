import subprocess

parameters = {"rocksdb.dir": "/mnt/vdc/rocksdb",
              "rocksdb.write_buffer_size": 10242424
              }
args = []
for k, v in parameters.items():
    args.append('-p')
    args.append("{}={}".format(k, v))
# args = ['-p', 'rocksdb.dir = /mnt/vdc/rocksdb']

# args.append("-P /root/zcj/go-ycsb/workloads/workloadb")
# proc = subprocess.Popen("go-ycsb run rocksdb -P /root/zcj/go-ycsb/workloads/workloadb -p r
# ocksdb.dir=/mnt/vdc/rocksd",
stdout=subprocess.PIPE)
proc = subprocess.Popen(['go-ycsb', 'run', 'rocksdb', '-P', '/root/zcj/go-ycsb/workloads/workloadb'] + args)
# proc = subprocess.Popen("go-ycsb run rocksdb -P /root/zcj/go-ycsb/workloads/workloadb",shell=True,stdout=subprocess.PIPE)
out, err = proc.communicate()

print(out)
