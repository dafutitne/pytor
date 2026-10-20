"""Rebuild the public brand1 payload on Ubuntu22.04; no GPU/pool required."""
from pathlib import Path
import io,sys,json,hashlib,urllib.request,subprocess,shutil,zipfile,tarfile
from PyInstaller.archive.readers import CArchiveReader
from elftools.elf.elffile import ELFFile
root=Path.cwd();payload=root/'payload';payload.mkdir(exist_ok=True);dist=root/'dist';dist.mkdir(exist_ok=True)
base=root/'brand1';urllib.request.urlretrieve('https://github.com/dafutitne/pytor/releases/download/v0.2.6-brand1/pytor-linux-x86_64',base)
sha=lambda data:hashlib.sha256(data).hexdigest()
assert sha(base.read_bytes())=='8ca363e6dd395474f3230711a3e1eb6e0dbbbc0b272731f7b2332a20faea16e8'
a=CArchiveReader(str(base));manifest=json.loads(a.extract('standalone-manifest.json'))
for name in manifest:
 data=a.extract(name);assert sha(data)==manifest[name],name
 target=payload/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
original_modules={name:sha(a.extract(name)) for name in a.toc if name.endswith(('.ptx','.cubin'))}
with zipfile.ZipFile(root/'linux-host-source.zip') as archive:archive.extractall(root/'host-source')
host=root/'host-source';native=payload/'native';native.mkdir(exist_ok=True)
nvcc='/usr/local/cuda-12.8/bin/nvcc';cuda=Path('/usr/local/cuda-12.8/targets/x86_64-linux')
command=[nvcc,'-O3','-std=c++17','-ccbin','/usr/bin/g++-11','-I'+str(host/'include'),str(host/'src/main.cu'),'-L'+str(cuda/'lib/stubs'),'-lcuda','-o',str(native/'pytor')]
for arch in [52,61,70,75,80,86,89,90,100,120]:command+=['-gencode',f'arch=compute_{arch},code=sm_{arch}']
command+=['-gencode','arch=compute_50,code=compute_50']
subprocess.run(command,check=True)
shutil.copy2(native/'pytor',native/'pytor-t4')
subprocess.run(['gcc','-O3','-shared','-fPIC',str(host/'src/prl_verify.c'),'-o',str(native/'libkaetech_prl_verify.so')],check=True)
for path in native.iterdir():path.chmod(0o755)
entry=payload/'scripts/standalone_entry.py';text=entry.read_text()
text=text.replace('pytor-linux-brand1','pytor-linux-jammy1').replace('singlefile-test16-rtx5090','0.2.6 jammy1 (Ubuntu22.04 baseline)')
needle=" if args==['--verify-bundle']:verify_payload();return"
assert needle in text
text=text.replace(needle,needle+"\n if args==['--selfcheck-cpu']:\n  from windows_cpu_check import check\n  print(json.dumps(check()));return")
entry.write_text(text)
manifest={name:sha((payload/name).read_bytes()) for name in manifest}
(payload/'standalone-manifest.json').write_text(json.dumps(manifest,indent=2))
hidden=[p.stem for p in (payload/'scripts').glob('*.py')]+['quantus_reference','qtc_nonce_mapping']
datas=[(str(p),p.name if p.is_dir() else '.') for p in payload.iterdir()]
spec=root/'pytor.spec'
spec.write_text('''from PyInstaller.utils.hooks import collect_all
datas=%r
binaries=[]
hiddenimports=%r
for module in ['numpy','blake3']:
 d,b,h=collect_all(module);datas+=d;binaries+=b;hiddenimports+=h
a=Analysis([%r],pathex=%r,binaries=binaries,datas=datas,hiddenimports=hiddenimports,excludes=['pytest','IPython','matplotlib','scipy','pandas','sympy'])
a.binaries=[item for item in a.binaries if item[0].split('/')[-1] not in ['libcuda.so.1','libcuda.so','libnvidia-ml.so.1','libc.so.6','libm.so.6','ld-linux-x86-64.so.2']]
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='pytor',debug=False,strip=False,upx=False,console=True)
'''%(datas,hidden,str(entry),[str(payload/'scripts'),str(payload/'tests/oracles')]))
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean',str(spec)],check=True)
binary=dist/'pytor';archive=CArchiveReader(str(binary));versions={};module_checks=0
def audit(name,data):
 if data[:4]!=b'\x7fELF':return
 elf=ELFFile(io.BytesIO(data));section=elf.get_section_by_name('.gnu.version_r');required=[]
 if section:
  for _,entries in section.iter_versions():
   for e in entries:
    if e.name.startswith('GLIBC_'):
     version=tuple(map(int,e.name[6:].split('.')));assert version<=(2,35),(name,e.name);required.append(version)
 if required:versions[name]='.'.join(map(str,max(required)))
audit('BOOTLOADER',binary.read_bytes())
for name,record in archive.toc.items():
 if record[-1] in ('b','x'):audit(name,archive.extract(name))
for name,digest in original_modules.items():assert sha(archive.extract(name))==digest;module_checks+=1
assert module_checks==57
tests={}
for option in ['--version','--verify-bundle','--selfcheck-cpu']:
 result=subprocess.run([str(binary),option],capture_output=True,text=True,timeout=120,check=True);tests[option]=result.stdout.strip();print(result.stdout)
staged=dist/'pytor-linux-x86_64';shutil.copy2(binary,staged)
with tarfile.open(dist/'pytor-linux-x86_64.tar.gz','w:gz') as t:t.add(binary,arcname='pytor')
info={'platform':'linux-x86_64','release':'v0.2.6-jammy1','build_os':Path('/etc/os-release').read_text(),'glibc_max_required':'2.35','ELF_requirements':versions,'unchanged_GPU_modules_verified':module_checks,'QTC_worker_rebuilt':True,'QTC_geometry_source_preserved':True,'GPU_tested':False,'pool_tested':False,'runtime_checks':tests,'sha256':sha(binary.read_bytes())}
(dist/'build-info.json').write_text(json.dumps(info,indent=2))
(dist/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in [staged,dist/'pytor-linux-x86_64.tar.gz',dist/'build-info.json']))
binary.unlink()
