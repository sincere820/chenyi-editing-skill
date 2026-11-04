"""Optional local Faster-Whisper transcription; output is an unverified transcript."""
import argparse,json
from pathlib import Path
from faster_whisper import WhisperModel
def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('output');ap.add_argument('--model',default='small');ap.add_argument('--offline',action='store_true');a=ap.parse_args()
    if Path(a.output).exists():raise FileExistsError('Keep original transcription; choose a new output')
    model=WhisperModel(a.model,device='cpu',compute_type='int8',local_files_only=a.offline)
    segments,info=model.transcribe(a.input,language='zh',beam_size=5,vad_filter=True,word_timestamps=True)
    rows=[dict(start=s.start,end=s.end,text=s.text,words=[dict(start=w.start,end=w.end,word=w.word,probability=w.probability) for w in s.words or []]) for s in segments]
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(dict(engine='faster-whisper',model=a.model,status='unverified',segments=rows),ensure_ascii=False,indent=2),encoding='utf-8')
    print(a.output)
if __name__=='__main__':main()
