import os
import unittest
import subprocess

_ASSETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','assets')


class TestCommand(unittest.TestCase):
    def __capture(self, cmd, check=True):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = p.communicate()

        if check is True and p.returncode != 0:
            raise Exception("Command failed ({}): {}\nOUTPUT:\n{}".format(p.returncode, cmd, output))

        return output.decode('utf-8'), p.returncode

    def test__search__simple1(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '7f']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (1438).

0000059e  ff 7f 0f 00 03 00 02 00  00 00 02 00 ff ff fb 01
"""

        self.assertEquals(output, expected)

    def test__search__simple2(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', '02', '00', 'ff']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (1448).

000005a8  02 00 ff ff fb 01 23 00  10 00 01 00 80 00 20 01
"""

        self.assertEquals(output, expected)

    def test__search__chunk1(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (0).

00000000  ff d8 ff e1 80 b0 45 78  69 66 00 00 49 49 2a 00
"""

        self.assertEquals(output, expected)

    def test__search__chunk2_via_search_offset(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '--search-start-offset', '1']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (2).

00000002  ff e1 80 b0 45 78 69 66  00 00 49 49 2a 00 08 00
"""

        self.assertEquals(output, expected)

    def test__search__chunk2_via_skip(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '--search-skip-count', '1']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (2).

00000002  ff e1 80 b0 45 78 69 66  00 00 49 49 2a 00 08 00
"""

        self.assertEquals(output, expected)

    def test__search__chunk3_via_skip(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '--search-skip-count', '2']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (1438).

0000059e  ff 7f 0f 00 03 00 02 00  00 00 02 00 ff ff fb 01
"""

        self.assertEquals(output, expected)

    def test__search__ff7f_chunk1(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '7f', '--search-skip-count', '0']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (1438).

0000059e  ff 7f 0f 00 03 00 02 00  00 00 02 00 ff ff fb 01
"""

        self.assertEquals(output, expected)

    def test__search__ff7f_chunk2(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '7f', '--search-skip-count', '1']
        output, _ = self.__capture(cmd)

        expected = """\
Found at (1494).

000005d6  ff 7f ff ff ff ff ff ff  00 00 ff ff 00 00 10 00
"""

        self.assertEquals(output, expected)

    def test__search__ff7f_chunk3_miss(self):
        cmd = ['bingrok', os.path.join(_ASSETS_PATH, 'NDM_8901.jpg'), '--search-bytes', 'ff', '7f', '--search-skip-count', '2']
        output, returncode = self.__capture(cmd, check=False)

        self.assertEquals(returncode, 2)
        self.assertEquals(output, "Bytes not found.\n")
