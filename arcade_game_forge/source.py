"""Closed C input profile: no host includes, assembly or preprocessor escapes."""
import json
import re


def check_source(source):
    if (type(source) is not str or not 1<=len(source.encode('utf-8'))<=65536 or
        not source.isascii() or any(ord(c)<32 and c not in '\n\r\t' for c in source) or
        '\\' in source or '??' in source):raise ValueError('bounded plain C source required')
    # Preserve literals: comment-looking text inside a C string is not a comment.
    tokens=re.compile(r'"[^"\n]*"|\x27[^\x27\n]*\x27|/\*.*?\*/|//[^\n]*',re.S)
    code=tokens.sub(lambda match:(' '+'\n'*match.group().count('\n'))
                    if match.group().startswith(('/*','//')) else match.group(),source)
    if '%:' in code:raise ValueError('preprocessor digraphs outside profile')
    if re.search(r'\b(?:asm|_Pragma|__[A-Za-z0-9_]*)\b',code):raise ValueError('assembly/pragma/builtin outside profile')
    includes=0
    for line in code.splitlines():
        line=line.strip()
        if not line.startswith('#'):continue
        if re.fullmatch(r'#\s*include\s+"lab_os\.h"',line):includes+=1;continue
        if re.fullmatch(r'#\s*define\s+[A-Z][A-Z0-9_]*\s+[0-9xXa-fA-FuUlL ()+*/%<>=!&|^~?:.,-]+',line):continue
        raise ValueError('only the SDK include and numeric defines are allowed')
    if includes!=1:raise ValueError('one lab_os.h include required')
    return source


def parse_response(response):
    if type(response) is not str or len(response.encode())>131072:raise ValueError('generator response size')
    def unique(pairs):
        result={}
        for name,value in pairs:
            if name in result:raise ValueError('duplicate response field')
            result[name]=value
        return result
    try:value=json.loads(response,object_pairs_hook=unique)
    except (ValueError,TypeError):raise ValueError('structured generator response required') from None
    if type(value) is not dict or set(value)!={'app_c'}:raise ValueError('only app_c may be generated')
    return check_source(value['app_c'])
