import json
import unittest
from arcade_game_forge.source import check_source, parse_response

GOOD='#include "lab_os.h"\n#define WIDTH 6u\nint value(void){return 2;}\n'

class SourceTests(unittest.TestCase):
    def test_basic_c_and_structured_output(self):
        self.assertEqual(check_source(GOOD),GOOD)
        self.assertEqual(parse_response(json.dumps(dict(app_c=GOOD))),GOOD)

    def test_host_file_includes_asm_pragmas_splices_and_unbounded_input_are_rejected(self):
        for code in (GOOD+'\n#include "/tmp/foreign"',GOOD+'\n#include NEXT',
                     GOOD+'\n#embed "/tmp/data"',GOOD+'\n#pragma once',
                     GOOD+'\nasm(".incbin data");',GOOD+'\n_Pragma("x")',
                     GOOD+'\n??/\n',GOOD+'\\\n',GOOD+'\0',GOOD+'x'*65536,
                     '#include "lab_os.h"\n#define HEAD "foreign"\n',
                     '#include "lab_os.h"\n__asm__("anything");'):
            with self.subTest(source=code[:40]),self.assertRaises(ValueError):check_source(code)

    def test_json_extra_duplicate_keys_fences_and_wrong_types_are_rejected(self):
        for response in ('```json\n{}\n```','{"app_c":3}',
                         json.dumps(dict(app_c=GOOD,claim='passed')),
                         '{"app_c":"first","app_c":"second"}'):
            with self.assertRaises(ValueError):parse_response(response)

    def test_string_comment_markers_and_c_digraphs_cannot_hide_host_includes(self):
        for source in (GOOD+'const char *a="/*";\n#include "/tmp/foreign"\nconst char *b="*/";',
                       GOOD+'\n%:include "/tmp/foreign"\n',
                       GOOD+'\nconst char *a="//";\n#include "/tmp/foreign"\n'):
            with self.assertRaises(ValueError):check_source(source)
