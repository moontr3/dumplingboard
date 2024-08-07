from typing import *


# functions

def shorten_string(string:str, max_chars:int=50, remove_newlines:bool=True) -> str:
    '''
    Strips the string.
    '''
    dots = False
    
    if len(string) > max_chars:
        dots = True
        string = string[:max_chars]
    
    if remove_newlines and '\n' in string:
        dots = True
        string = string.split('\n')[0]

    return string+('...' if dots else '')

    