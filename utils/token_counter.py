#Count the number of tokens in a given text using OpenAI's tokenizer.

import tiktoken

def num_tokens_from_string(string, encoding_name): #Returns the number of tokens in a text string using TikToken's encoding.

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))

def count_thread_tokens(thread_id, client, encoding_name): #Count the total number of tokens in a thread.
    
    messages = client.beta.threads.messages.list(thread_id=thread_id).data
    total_tokens = sum(num_tokens_from_string(message.content[0].text.value, encoding_name) for message in messages)
    return total_tokens

