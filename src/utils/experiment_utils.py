import re, json
import logging

import sys
import threading
from time import sleep
try:
    import thread
except ImportError:
    import _thread as thread

try:
    range, _print = xrange, print
    def print(*args, **kwargs): 
        flush = kwargs.pop('flush', False)
        _print(*args, **kwargs)
        if flush:
            kwargs.get('file', sys.stdout).flush()            
except NameError:
    pass


def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    # print('{0} took too long'.format(fn_name), file=sys.stderr)
    # sys.stderr.flush() # Python 3 stderr is likely buffered.
    thread.interrupt_main() # raises KeyboardInterrupt


def exit_after(s):
    '''
    use as decorator to exit process if 
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer


class HTTPRequestFilter(logging.Filter):
    def filter(self, record):
        return not re.search(r'HTTP Request', record.getMessage())

def load_from_jsonl(file_path):
    with open(file_path, 'r') as file:
        return [json.loads(line) for line in file]
    
def load_from_jsonl_nonlist(file_path):
    with open(file_path, 'r') as file:
        return [line for line in json.loads(file.read())]
    
def extract_functions(generated_text):
    # match any function name containing "successor" or similar variations
    successor_pattern = re.compile(r"```(?:python)?\n(.*?def.*?successor.*?\(.*?\).*?\n.*?```)", re.DOTALL | re.IGNORECASE)
    goal_pattern = re.compile(r"```(?:python)?\n(.*?def.*?goal.*?\(.*?\).*?\n.*?```)", re.DOTALL | re.IGNORECASE)
    
    successor_code = successor_pattern.search(generated_text)
    # Remove the surrounding triple backticks from the matched code blocks and the optional language specifier
    successor_code = successor_code.group(1).strip("```").strip() if successor_code else None
    if successor_code:
        return successor_code

    goal_code = goal_pattern.search(generated_text)
    # Remove the surrounding triple backticks from the matched code blocks and the optional language specifier
    goal_code = goal_code.group(1).strip("```").strip() if goal_code else None
    return goal_code


def parse_functions(generated_text):
    def get_row_index(rows, text):
        c = 0
        while c < len(rows):                
            if rows[c].startswith(text):
                return c
            c +=1
        return None
    def extract(r):
        # 1. Remove the rows after the end of the function scope
        # 2. Take the rows before the first def, indent them and add to after the first def
        rows = r.split("\n")
        c = get_row_index(rows, "def ")
        if c is None:
            return ""
        # Checking for successor or goal in function name
        if "successor" not in rows[c].lower() and "goal" not in rows[c].lower():
            return ""
        includes = [f"    {r}" for r in rows[:c]]
        # Finding the end of function scope by finding the first row after def that is not indented
        new_rows = ["@exit_after(1)"] + rows[c:c+1] + includes
        for r in rows[c+1:]:
            if len(r) > 0 and r[0].isalpha():
                break
            new_rows.append(r)
                        
        return "\n".join(new_rows)

    generated_text = generated_text.replace("<|endoftext|>", "")
    arr = generated_text.split("```")
    if len(arr) == 1:
        r = arr[0]
        if r.startswith("python") or r.startswith("Python"):
            r=r[6:].strip()
        text = extract(r)
        if len(text) == 0:
            return None
        return text        
    
    # Odd places should contain the code snippets
    for i, r in enumerate(arr):
        if i % 2 == 0:
            continue
        if "def " not in r:
            continue 
        
        if r.startswith("python") or r.startswith("Python"):
            r=r[6:].strip()
        
        text = extract(r)
        if len(text) == 0:
            continue
        return text

def get_function_by_keyword(function_code, keyword):
    pattern = re.compile(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*\):")
    matches = pattern.findall(function_code)
    for match in matches:
        if keyword.lower() in match.lower():
            return match
    return None

def get_from_text_by_keyword(text, keyword):
    # function_text = extract_functions(text)
    if not text.strip():
       return None, None, None
    function_text = parse_functions(text)
    if function_text:
        code = function_text.strip('```')
        # Wrap with try and give feedback if fails on SyntaxError
        try:
            exec(code)
        except SyntaxError as e:
            return None, None, e
        function_name = get_function_by_keyword(code, keyword)
        if function_name:
            return locals().get(function_name, None), code, None
    return None, None, None

