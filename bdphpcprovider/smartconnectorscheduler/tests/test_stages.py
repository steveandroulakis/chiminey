# Copyright (C) 2013, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import os
import tempfile
import unittest
import logging
import logging.config
from bdphpcprovider.smartconnectorscheduler.management.commands import view


logger = logging.getLogger(__name__)


def unix_find(pathin):
    """Return results similar to the Unix find command run without options
    i.e. traverse a directory tree and return all the file paths
    from http://www.saltycrane.com/blog/2010/04/options-listing-files-directory-python/
    """
    return [os.path.join(path, file)
            for (path, dirs, files) in os.walk(pathin, followlinks=True)
            for file in files]


class TestOutputView(unittest.TestCase):
    """
    """

    keep_directories = False

    def setUp(self):
        self.view_dir = tempfile.mkdtemp()
        logger.debug("view_dir=%s" % self.view_dir)
        self.output_dir = os.path.join("smartconnectorscheduler", "testing", "outputdir")
        logger.debug("output_dir=%s" % self.output_dir)

    def tearDown(self):
        if not self.keep_directories:
            import shutil
            shutil.rmtree(self.view_dir)
        else:
            logger.warn("Keeping directory %s" % self.keep_directories)
        pass

    def test_view(self):
        view.convert_output(self.output_dir, self.view_dir)
        view_dir_walk = list(unix_find(self.view_dir))
        from pprint import pformat
        logger.debug("view_dir_walk= %s" % pformat(view_dir_walk))

        view_dir_walk = sorted([x[len(self.view_dir):] for x in view_dir_walk])
        from pprint import pformat
        logger.debug("vie_dir_walk= %s" % pformat(view_dir_walk))
        correct = [
             '/input/input_0/initial/rmcen.inp_values',
             '/input/input_1/node1/rmcen.inp_values',
             '/input/input_2/node1/rmcen.inp_values',
             '/input/input_3/node2/rmcen.inp_values',
             '/output/0_0/rmcen.inp_values',
             '/output/0_1/rmcen.inp_values',
             '/output/1b0/rmcen.inp_values',
             '/output/1b1/rmcen.inp_values',
             '/output/2a0/rmcen.inp_values',
             '/output/2a1/rmcen.inp_values',
             '/raw/input_0/initial/rmcen.inp_values',
             '/raw/input_1/node1/rmcen.inp_values',
             '/raw/input_2/node1/rmcen.inp_values',
             '/raw/input_3/node2/rmcen.inp_values',
             '/raw/output_0/node1/rmcen.inp_values',
             '/raw/output_0/node2/rmcen.inp_values',
             '/raw/output_1/node1/rmcen.inp_values',
             '/raw/output_1/node2/rmcen.inp_values',
             '/raw/output_2/node1/rmcen.inp_values',
             '/raw/output_2/node2/rmcen.inp_values']
        self.assertEquals(correct, view_dir_walk)


