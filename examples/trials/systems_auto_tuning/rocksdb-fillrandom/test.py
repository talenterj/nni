import subprocess


# args = ['-P /root/zcj/go-ycsb/workloads/workloadb']
args = ['rocksdb.write_buffer_size=64']

#args.append("-P /root/zcj/go-ycsb/workloads/workloadb")
#proc = subprocess.Popen("go-ycsb run rocksdb -P /root/zcj/go-ycsb/workloads/workloadb -p rocksdb.dir=/mnt/vdc/rocksd", stdout=subprocess.PIPE)
proc = subprocess.Popen(['go-ycsb', 'run', 'rocksdb', '-P', '/root/zcj/go-ycsb/workloads/workloadb', '-p'] + args, stdout=subprocess.PIPE)
# proc = subprocess.Popen("go-ycsb run rocksdb -P /root/zcj/go-ycsb/workloads/workloadb",shell=True,stdout=subprocess.PIPE)
out, err = proc.communicate()

print(out)