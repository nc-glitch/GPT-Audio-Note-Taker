import re
import math
import openai
openai.api_key = 'your_key'
'''
engine: The name of the language model to use. The default value is "davinci-codex".
max_tokens: The maximum number of tokens to generate in the completion. The default value is 1024.
n: The number of completions to generate. The default value is 1.
stop: A string or list of strings that specifies tokens at which to stop generation. The default value is None.
temperature: Controls the “creativity” of the generated text. Higher values result in more creative output. The default value is 0.7.
frequency_penalty: Controls how often the model repeats itself in the generated text. Higher values result in less repetition. The default value is 0.
presence_penalty: Controls how often the model generates output that is not present in the input prompt. Higher values result in more conservative output. The default value is 0.
context: A string or list of strings that provides context for the completion. The default value is an empty string.
'''
#gpt-4: engine='davinci-codex-002'

basic_model_role = 'You are a helpful and concise assistant who turns lectures into notes for studying. The transcription ' \
"is imperfect, so make sure to use context clues and logical thinking to account for transcription errors. Make the notes much shorter than the original lecture: only focus on key info"
prompting_text = "Consider the lecture's topic: how it functions, what are its impacts, applications, and challenges?"
summary_role = 'You are a helpful and concise assistant who takes notes and summarizes where they left off for easy continuation.' \
    'Please make sure to restate the general topic of the lecture and the subtopic that was last discussed and where it was left off.' \


model = "gpt-3.5-turbo"

def prompt(transcript, previous_summary='', intro_info='', supplemental_info='', new_model="gpt-3.5-turbo", top_p=.1, min_reduction_factor=5):
    global model
    if new_model != model:
        model = new_model

    tokens = len(re.findall(r'\w+', transcript))  # max-tokens just cuts the model off - not worth using more than an abs max
    if tokens >= 7990:
        model += '-16k'
    max_tokens = max(tokens, 50)

    model_role = basic_model_role + intro_info + prompting_text
    if intro_info.lower() == 'no':
        model_role = ''

    if not previous_summary:
        supplemental_info = 'This transcript is only a portion of the lecture, divided because the lecture was too long.' \
        ' the lecture left off discussing:' + previous_summary + '\n other info worth noting:' + supplemental_info

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
                # providing the system its role
                {"role": "system", "content": model_role},

                # the user's query of the system
                {"role": "user", "content": transcript},

                # helpful information
                {"role": "assistant", "content": supplemental_info},
        ],
        top_p = top_p,  # nucleus-sampling stat: only considers tokens with the top_p probability
        max_tokens = max_tokens
        # to-try: presence_penalty & frequency_penalty
    )
    return response

def left_off(notes, new_model="gpt-3.5-turbo", top_p=.1, min_reduction_factor=5):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
                # providing the system its role
                {"role": "system", "content": summary_role},

                # the user's query of the system
                {"role": "user", "content": transcript},

                # helpful information
                {"role": "assistant", "content": supplemental_info},
        ],
        top_p = top_p,  # nucleus-sampling stat: only considers tokens with the top_p probability
        max_tokens = max_tokens
        # to-try: presence_penalty & frequency_penalty
    )
    return response


def find_sentence_end(tokens, idx):
    end_chars = tokens[idx][-1]
    while end_chars != '.' or end_chars != '?' or end_chars != '!':
        idx += 1
        end_chars = tokens[idx][-1]
    return idx

def find_frags(tokens):
    num = math.ceil(tokens / 8_000)
    seg_len = math.ceil(tokens / num)

    idxs = [0]
    for i in range(1, num + 1):
        idxs.append(find_sentence_end(tokens, i * seg_len))

    frags = []
    for i in range(1, len(idxs)):
        frag = tokens[idxs[i - 1]: idxs[i]]
        frags.append(' '.join(frag))

    return frags

def to_text(response):
    return  response['choices'][0]['message']['content'].strip()

def response_to_text(transcript, intro_info='', supplemental_info='', new_model="gpt-3.5-turbo", top_p=.1, min_reduction_factor=5):
    transcript = transcript.replace("..", ".").replace("?.", "?").replace("!.", "!")
    tokens = transcript.split()
    tokens_len = len(tokens)
    if tokens_len > 2_000:
        model += '-16k'
    if tokens_len > 8_000:
        parts = find_frags(transcript)
    else:
        parts = [' '.join(tokens)]
    if len(parts) == 1:
        response = prompt(parts[0], previous_summary='', intro_info=intro_info, supplemental_info=supplemental_info, new_model=new_model, top_p=top_p, min_reduction_factor=min_reduction_factor)
        return response['choices'][0]['message']['content'].strip()

    previous_summary = ""
    for part in parts:
        response = prompt(part, previous_summary=previous_summary, intro_info=intro_info, supplemental_info=supplemental_info, new_model=new_model, top_p=top_p, min_reduction_factor=min_reduction_factor)
        previous_summary = left_off(to_text(response))
        previous_summary = to_text(previous_summary)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pass
    print(response_to_text("what's 2 + 2"))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

'''
3Q / Year: 12 Weeks/ Q: 8 lectures per week: 
    120 min / lecture:
        12,000 tokens input / lecture:
        1,200 tokens outut / lecture:
        
-> 288 lectures / Year:
    -> 3,456,000 tokens in
    -> 345,600 tokens out
    

'''