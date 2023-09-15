
'''
POSSIBLE Services:
    Google Dynamic Batch Speech Recognition: https://cloud.google.com/speech-to-text
        Won't process immediately, but it's cheap and I won't have to wait longer than 2 hours
    ElevateAI: https://www.elevateai.com/pricing/
    SpeechNotes: https://www.speechnotes.co
    Whipser: 240 / year -> 27 / month: https://openai.com/research/whisper
    HabbyScribe: 12 / Month: https://www.happyscribe.com/

    Faster-Whisper: https://github.com/guillaumekln/faster-whisper/tree/master/tests
    https://pypi.org/project/faster-whisper/#:~:text=faster-whisper%20is%20a%20reimplementation%20of%20OpenAI%27s%20Whisper%20model,with%208-bit%20quantization%20on%20both%20CPU%20and%20GPU.

'''

from faster_whisper import WhisperModel
model_size = 'large-v2'

# REQUIRES Nvidea cuBLASS (not supported on windows)
# Run on GPU with FP16
#model = WhisperModel(model_size, device="cuda", compute_type="float16")
# or run on GPU with INT8
#model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

# or run on CPU with INT8
model = WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe(audio_file, vad_filter=True, vad_filter_time=200, beam_size=5):
    if audio_file.split(sep='.')[-1] != "mp3":
        print('Wrong Format')
        # TODO: implement proper exception class
    # vad_filter: filters for parts without speech (defualt is 2s, can change with vad_parameters=dict(min_silence_duration_ms=time)
    # beam_size: number of transcription possibilities simultaneously tracked (the best sequence is returned)
    if vad_filter:
        segments, info = model.transcribe(audio_file, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=vad_filter_time), beam_size=beam_size)
    else:
        segments, info = model.transcribe(audio_file, beam_size=beam_size)
    segments = list(segments)
    return segments, info

def transcribe_text(audio_file, vad_filter=True, vad_filter_time=200, beam_size=5):
    transcription, _ = transcribe(audio_file, vad_filter=vad_filter, vad_filter_time=vad_filter_time, beam_size=beam_size)
    text = [segment.text.strip() for segment in transcription]
    # text = '.\n\n'.join(text)
    return text

if 0:
    import os
    from pydub import AudioSegment
    def switch_to_mp3(audio_file):
        form = audio_file.split(sep='.')[-1]
        new_name = audio_file.split(sep='.')[:-1]
        new_name = '.'.join(new_name) + '.mp3'
        alt_audio = AudioSegment.from_file(audio_file, form)
        alt_audio.export(new_name, format='mp3')
        #os.remove(audio_file)
        return new_name

    import subprocess
    def switch_to_mp3_better(audio_file):
        audio_file = pwd() + '\\' + audio_file
        print(audio_file)
        form = audio_file.split(sep='.')[-1]
        new_name = audio_file.split(sep='.')[:-1]
        new_name = '.'.join(new_name) + '.mp3'
        subprocess.run(["ffmpeg", "-i", audio_file, "-codec:a", "libmp3lame", "-qscale:a", "2", new_name])
        return new_name

    def pwd():
        return os.getcwd()

if __name__ == '__main__':
    transcription = transcribe_text('test.mp3', vad_filter_time=200)
    print(transcription)



