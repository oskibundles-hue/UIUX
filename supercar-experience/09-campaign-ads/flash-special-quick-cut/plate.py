import subprocess, sys
FF=sys.argv[1]
CUTS={
 # (src_in, src_out, speed)  speed<1 = slower; total must be 15.0 s
 'gt3rs':('GT3RS_livery.mov',[(5.05,6.45,1),(3.10,4.50,1),(0.34,0.99,1),(6.98,7.41,1),(7.43,7.85,1),
          (1.01,1.91,1),(9.39,10.58,1),(8.18,8.58,1),(10.60,11.11,1),
          (1.93,3.03,1),(7.85,8.16,1),(8.60,9.37,1),(11.15,11.97,1),
          (12.10,13.95,1.85/5.10)]),
 'bs':('BlackSeries.mov',[(0.30,1.80,1),(8.10,9.50,1),(13.00,14.50,1),(2.43,5.43,1),
          (10.44,12.94,1),(1.93,2.41,1),(15.08,17.80,2.72/4.62)]),
}
car=sys.argv[2]; src,segs=CUTS[car]
f=[];c=''
for i,(a,b,sp) in enumerate(segs):
    f.append(f"[0:v]trim=start={a}:end={b},setpts=(PTS-STARTPTS)/{sp},format=yuv420p,fps=24[v{i}]"); c+=f'[v{i}]'
fc=';'.join(f)+f";{c}concat=n={len(segs)}:v=1:a=0,trim=duration=15,eq=contrast=1.05:saturation=1.05[out]"
tot=sum((b-a)/sp for a,b,sp in segs); print(car,'total',round(tot,3))
subprocess.run([FF,'-hide_banner','-loglevel','error','-y','-i',sys.argv[3] if len(sys.argv)>3 else f'../footage/{src}','-filter_complex',fc,'-map','[out]','-c:v','libx264','-crf','14','-preset','veryfast','-pix_fmt','yuv420p','-r','24',f'plate_{car}.mp4'],check=True)
