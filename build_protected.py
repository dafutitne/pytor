"""Build Linux protection release on Ubuntu22; only the recipient public key is an input."""
from pathlib import Path
import hashlib,io,json,os,shutil,subprocess,sys,tarfile,urllib.request,zipfile
from PyInstaller.archive.readers import CArchiveReader
from elftools.elf.elffile import ELFFile
from setuptools import Extension,Distribution
from Cython.Build import cythonize
from Cython.Compiler import Options
root=Path.cwd();r=root/'protection';r.mkdir(exist_ok=True);dist=root/'dist';dist.mkdir(exist_ok=True)
with zipfile.ZipFile(root/'protection-patch.zip') as z:z.extractall(r)
sha=lambda data:hashlib.sha256(data).hexdigest()
base=r/'jammy3';urllib.request.urlretrieve('https://github.com/dafutitne/pytor/releases/download/v0.2.6-jammy3/pytor-linux-x86_64',base)
assert sha(base.read_bytes())=='1f75b8dddf12c363abbe1bbf2d73e1489a849f48062c9cf9961694c716e289c7'
old=CArchiveReader(str(base));manifest=json.loads(old.extract('standalone-manifest.json'));original_modules={}
for name,digest in manifest.items():
 data=old.extract(name);assert sha(data)==digest,name
 p=r/'base-payload'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 if name.endswith(('.ptx','.cubin')) or name.startswith('native/'):original_modules[name]=digest
(r/'base-payload/standalone-manifest.json').write_bytes(old.extract('standalone-manifest.json'))
subprocess.run([sys.executable,str(r/'prepare_payload.py')],check=True)
payload=r/'payload';scripts=payload/'scripts';shutil.copy2(r/'log-public.pem',payload/'log-public.pem')
assert b'PUBLIC KEY' in (payload/'log-public.pem').read_bytes() and b'PRIVATE KEY' not in (payload/'log-public.pem').read_bytes()
modules=['branding','cuda_driver','exclusive_gpu','gpu_profiles','mine_prl','mine_qtc','prl_components','prl_engine','prl_fast','prl_legacy_abi','prl_protocol','qtc_driver_worker','qtc_job','recovered_kernel_abi','secure_log','protected_app','windows_cpu_check','qtc_nonce_mapping','quantus_reference','qtc_selfcheck']
Options.docstrings=False
extensions=[Extension(name,[str(scripts/(name+'.py'))],extra_compile_args=['-O2','-g0','-fvisibility=hidden','-fstack-protector-strong'],extra_link_args=['-Wl,-z,relro,-z,now']) for name in modules]
compiled=cythonize(extensions,compiler_directives={'language_level':3,'binding':False,'annotation_typing':False,'embedsignature':False,'infer_types':False},nthreads=2,build_dir=str(r/'cython-c'))
setup=Distribution({'name':'pytor-protected','ext_modules':compiled});cmd=setup.get_command_obj('build_ext');cmd.build_lib=str(scripts);cmd.build_temp=str(r/'obj');cmd.ensure_finalized();cmd.run()
for so in scripts.glob('*.so'):subprocess.run(['strip','--strip-unneeded',str(so)],check=True)
assert len(list(scripts.glob('*.so')))==len(modules)
for folder in [scripts,payload/'tests',payload/'tests/oracles']:
 for p in folder.glob('*.py'):p.unlink()
 for p in folder.glob('__pycache__'):
  if p.is_dir():shutil.rmtree(p)
assert not list(payload.rglob('*.py'))
sys.path.insert(0,str(r));import checks
crypto_checks=checks.run(scripts)
(dist/'crypto-checks.json').write_text(json.dumps(crypto_checks,indent=2))
new_manifest={str(p.relative_to(payload)).replace(os.sep,'/'):sha(p.read_bytes()) for p in payload.rglob('*') if p.is_file() and p.name!='standalone-manifest.json'}
for name,digest in original_modules.items():assert new_manifest[name]==digest,name
(payload/'standalone-manifest.json').write_text(json.dumps(new_manifest,indent=2))
datas=[(str(p),p.name if p.is_dir() else '.') for p in payload.iterdir() if p.name!='scripts']
binaries=[(str(p),'scripts') for p in scripts.glob('*.so')]
hidden=modules+['argparse','base64','ctypes','gzip','hmac','importlib','io','json','select','socket','struct','subprocess','tempfile','threading','traceback','dataclasses','concurrent.futures','cryptography.hazmat.primitives.asymmetric.x25519','cryptography.hazmat.primitives.kdf.hkdf','cryptography.hazmat.primitives.ciphers.aead']
spec=root/'pytor-protected.spec'
spec.write_text('''from PyInstaller.utils.hooks import collect_all
datas=%r
binaries=%r
hiddenimports=%r
for module in ['numpy','blake3','cryptography']:
 d,b,h=collect_all(module);datas+=d;binaries+=b;hiddenimports+=h
a=Analysis([%r],pathex=[%r],binaries=binaries,datas=datas,hiddenimports=hiddenimports,excludes=['pytest','IPython','matplotlib','scipy','pandas','sympy','Cython','setuptools'])
appmods=set(%r)
assert not any(row[0] in appmods for row in a.pure)
fixed={}
for name,path,kind in a.binaries:
 if name.split('/')[-1].split('.')[0] in appmods:name='scripts/'+name.split('/')[-1]
 if name.split('/')[-1] in ['libcuda.so.1','libcuda.so','libnvidia-ml.so.1','libc.so.6','libm.so.6','ld-linux-x86-64.so.2']:continue
 fixed[name]=(name,path,kind)
a.binaries=list(fixed.values())
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='pytor',debug=False,strip=False,upx=False,console=True)
'''%(datas,binaries,hidden,str(r/'loader.py'),str(scripts),modules))
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean',str(spec)],check=True)
binary=dist/'pytor';archive=CArchiveReader(str(binary));pyz=archive.open_embedded_archive('PYZ.pyz')
assert not any(name in pyz.toc for name in modules)
assert not any(name.endswith('.py') for name in archive.toc if name.startswith(('scripts/','tests/')))
for name,digest in original_modules.items():assert sha(archive.extract(name))==digest,name
for name,digest in new_manifest.items():assert sha(archive.extract(name))==digest,name
assert not any('private.pem' in n.lower() for n in archive.toc)
glibc={}
def audit(name,data):
 if data[:4]!=b'\x7fELF':return
 elf=ELFFile(io.BytesIO(data));section=elf.get_section_by_name('.gnu.version_r');required=[]
 if section:
  for _,entries in section.iter_versions():
   for entry in entries:
    if entry.name.startswith('GLIBC_'):
     version=tuple(map(int,entry.name[6:].split('.')));assert version<=(2,35),(name,entry.name);required.append(version)
 if required:glibc[name]='.'.join(map(str,max(required)))
audit('BOOTLOADER',binary.read_bytes())
for name,record in archive.toc.items():
 if record[-1] in ('x','b'):audit(name,archive.extract(name))
runtime={}
for option in ['--version','--verify-bundle','--selfcheck-cpu']:
 test=subprocess.run([str(binary),option],capture_output=True,timeout=180)
 assert test.returncode==0,(option,test.stderr[-300:]);runtime[option]={'exit':test.returncode,'encrypted_lines':sum(line.startswith(b'PLOG1:') for line in (test.stdout+test.stderr).splitlines())}
 if option=='--selfcheck-cpu':assert all(line.startswith(b'PLOG1:') for line in (test.stdout+test.stderr).splitlines())
 (dist/(option[2:]+'.log')).write_bytes(test.stdout+test.stderr)
bad=subprocess.run([str(binary),'--algorithm','pearlhash','--pool','localhost:1','--wallet','PRIVATE_SMOKE_WALLET'],capture_output=True,timeout=40)
assert bad.returncode!=0 and b'PRIVATE_SMOKE_WALLET' not in bad.stdout+bad.stderr
assert all(line.startswith(b'PLOG1:') for line in (bad.stdout+bad.stderr).splitlines())
runtime['encrypted_GPU_init_failure']={'exit':bad.returncode,'encrypted':True}
(dist/'startup-failure.log').write_bytes(bad.stdout+bad.stderr)
info={'release':'v0.2.7-protect1','base_release':'v0.2.6-jammy3','sha256':sha(binary.read_bytes()),'compiled_host_modules':modules,'app_source_or_bytecode_in_payload':False,'unchanged_GPU_modules':57,'original_native_workers_unchanged':True,'log_cipher':'X25519 + HKDF-SHA256 + ChaCha20-Poly1305','recipient_key_id':json.loads((r/'public-key-info.json').read_text())['recipient_key_id'],'private_key_in_release':False,'hardware_license':False,'ELF_GLIBC_requirements':glibc,'runtime_checks':runtime,'crypto_checks':crypto_checks,'GPU_tested':False,'pool_tested':False,'limitations':['Native code and GPU kernels remain recoverable by skilled reverse engineering','Old public releases are not retroactively protected','OS and bootloader errors before Python loads are outside encrypted application logging']}
(dist/'build-info.json').write_text(json.dumps(info,indent=2))
shutil.copy2(binary,dist/'pytor-linux-x86_64');shutil.copy2(r/'decrypt_logs.py',dist/'decrypt_logs.py')
with tarfile.open(dist/'pytor-linux-x86_64.tar.gz','w:gz') as t:t.add(binary,arcname='pytor')
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--name','pytor-log-reader',str(r/'decrypt_logs.py')],check=True)
reader=dist/'pytor-log-reader';subprocess.run([str(reader),'--help'],check=True,capture_output=True,timeout=60)
audit('pytor-log-reader',reader.read_bytes())
(dist/'SHA256SUMS').write_text(''.join(f'{sha((dist/n).read_bytes())}  {n}\n' for n in ['pytor-linux-x86_64','pytor-linux-x86_64.tar.gz','pytor-log-reader','decrypt_logs.py','build-info.json','crypto-checks.json']))
binary.unlink();print('PROTECTED_BUILD_COMPLETE',info['sha256'],flush=True)
