from transcription import transcribe_text
import google_interface as gi
import query_gpt as qgpt
import os

def find_mid_gap(text):
    tokens = text.split()
    pointer = len(tokens)//2

    end_chars = tokens[pointer][-2:]
    while end_chars != '..' or end_chars != '?.' or end_chars != '!.':
        pointer += 1
        end_chars = tokens[pointer][-2:]

    first_half = tokens[:pointer]
    first_half = ' '.join(first_half)
    second_half = tokens[:pointer]
    second_half = ' '.join(second_half)
    return first_half, second_half

def run(output_name = 'notes.txt'):
    if 0:
        files_to_transcribe = gi.get_files_to_process()

        for folder in files_to_transcribe:
            mp3_id = folder[0][0]
            mp3_name = folder[0][1]
            parent_id = folder[0][2]
            gi.download_file(mp3_id, mp3_name)

            print('Transcribing...')
            transcription = transcribe_text(mp3_name)
            os.remove(mp3_name)
            print('Transcription Complete')
            with open('transcript.txt', 'w') as file:
                for line in transcription:
                    file.write(f'{line} \n')

            info = ''
            if len(folder) > 1:
                info_id = folder[1][0]
                info_name = folder[1][1]
                gi.download_file(info_id, info_name)

                with open(info_name, 'r') as file:
                    info = file.readlines()
                os.remove(info_name)
                info = '\n'.join(info)

    transcription = ''
    with open('transcript.txt', 'r') as file:
        transcription = file.readline()
    info = ''

    notes = qgpt.response_to_text(transcription, supplemental_info=info)

    with open(output_name, 'w') as file:
        file.writelines(notes)
    gi.upload_file(output_name, parent_id)
    os.remove(output_name)

    return notes


if __name__ == '__main__':
    notes = run()
    print('Here Are The Notes:')
    print(notes)


if 0:
    audiofile_name = 'test'
    audiofile = audiofile_name + '.mp3'
    transcription = transcribe_text(audiofile)
    print("Transcription Complete\nTaking Notes...")
    text = '.\n'.join(transcription)
    print(text)

    notes = qgpt.response_to_text(text)
    print('Notes:\n')
    print(notes)

