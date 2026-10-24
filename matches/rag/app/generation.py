"""Keep interrupted image generations out of the persistent document index."""
import time


class IncompleteGeneration(RuntimeError):
    pass


def ended(last_token,eos_token_ids):
    if eos_token_ids is None:return False
    if isinstance(eos_token_ids,int):eos_token_ids=[eos_token_ids]
    return last_token in eos_token_ids


def transcribe_complete(generate,messages,deadline,clock=time.monotonic):
    for limit,tokens in [(40,768),(20,1536)]:
        remaining=deadline-clock()
        if remaining<1:raise TimeoutError('Image OCR indexing deadline reached')
        try:
            return generate(messages,max_tokens=tokens,seconds=min(limit,remaining),require_complete=True)
        except IncompleteGeneration:
            continue
    raise IncompleteGeneration('Image transcription remained incomplete after one retry')
