"""Create a local rehearsal video with disclosed macOS synthetic speech, not a submitted video."""
from pathlib import Path
import json,subprocess,shutil
from PIL import Image, ImageDraw, ImageFont
R=Path(__file__).resolve().parents[1]; B=R/'.build/video';B.mkdir(parents=True,exist_ok=True)
speeches=json.loads((R/'slides/narration.json').read_text()); timeline=[];start=0
for i,txt in enumerate(speeches,1):
 f=B/f'narration-{i}.txt';f.write_text(txt);a=B/f'narration-{i}.aiff';out=B/f'segment-{i}.mp4'
 subprocess.run(['say','-v','Samantha','-r','145','-f',str(f),'-o',str(a)],check=True)
 dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(a)],text=True))+1.1
 image=R/'slides/previews'/f'slide-{i}.png'
 # The visible label identifies the synthesized rehearsal throughout.
 im=Image.open(image).convert('RGB').resize((1920,1080))
 draw=ImageDraw.Draw(im); font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
 draw.text((1894,1055),'REHEARSAL - SYNTHETIC VOICE',font=font,fill='#7B8B90',anchor='ra')
 labeled=B/f'slide-{i}.png';im.save(labeled); image=labeled
 vf='scale=1920:1080'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','12','-i',str(image),'-i',str(a),'-vf',vf,'-c:v','libx264','-preset','fast','-tune','stillimage','-crf','23','-pix_fmt','yuv420p','-af','apad=pad_dur=1.1','-c:a','aac','-b:a','128k','-t',str(dur),'-movflags','+faststart',str(out)],check=True)
 timeline.append({'slide':i,'start_seconds':start,'duration_seconds':dur,'voice':'macOS Samantha synthetic'});start+=dur;print(f'Slide {i}: {dur:.1f}s',flush=True)
(B/'concat.txt').write_text(''.join(f"file '{(B/f'segment-{i}.mp4').as_posix()}'\n" for i in range(1,7)))
final=R/'slides/rehearsal.mp4';subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(B/'concat.txt'),'-c','copy','-movflags','+faststart',str(final)],check=True)
actual=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(final)],text=True));assert actual<300,actual
(R/'slides/video_timing.json').write_text(json.dumps({'duration_seconds':actual,'synthetic_voice':True,'submitted':False,'timeline':timeline},indent=2));print('Duration',actual,flush=True)
