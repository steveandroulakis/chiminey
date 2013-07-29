
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

import json
import ast
import re
import logging
import os
import logging.config
from itertools import product


from bdphpcprovider.smartconnectorscheduler.smartconnector import (
    Stage, get_url_with_pkey)
from bdphpcprovider.smartconnectorscheduler import hrmcstages
from bdphpcprovider.smartconnectorscheduler import smartconnector

from django.template import Context, Template


from . import setup_settings

logger = logging.getLogger(__name__)


class MakeUploadStage(Stage):
    """
    copies directories from one location to another
    """
    def __init__(self, user_settings=None):
        pass

    def input_valid(self, settings_to_test):
        return (True, "ok")

    def triggered(self, run_settings):
        if self._exists(
                run_settings,
                'http://rmit.edu.au/schemas/stages/upload_makefile',
                'done'):
            upload_makefile_done = int(run_settings[
                'http://rmit.edu.au/schemas/stages/upload_makefile'][u'done'])
            return not upload_makefile_done
        return True

    def process(self, run_settings):
        """ perform the stage operation
        """

        settings = setup_settings(run_settings)
        logger.debug("settings=%s" % settings)
        self.runs_left = _upload_variations_inputs(
            settings,
            settings['input_location'])

    """
        remote_path = "%s@%s_%s" % ("nci",
                                     settings['payload_destination'],
                                     settings['contextid'])
        logger.debug("Relative path %s" % remote_path)
        encoded_d_url = smartconnector.get_url_with_pkey(
            settings,
            remote_path,
            is_relative_path=True,
            ip_address=run_settings[
                models.UserProfile.PROFILE_SCHEMA_NS]['nci_host'])
        logger.debug("destination_url=%s" % encoded_d_url)
        hrmcstages.copy_directories(encoded_s_url, encoded_d_url)
    """

    def output(self, run_settings):
        """ produce the resulting datfiles and metadata
        """
        logger.debug("CopyDirectory Stage Output")
        logger.debug("run_settings=%s" % run_settings)
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/upload_makefile',
            {})[u'done'] = 1
        run_settings.setdefault(
            'http://rmit.edu.au/schemas/stages/make',
            {})[u'runs_left'] = str(self.runs_left)
        return run_settings


def _upload_variations_inputs(settings, source_url):

    #variation_map = {'a': [3]}

    variation_map = ast.literal_eval(settings['sweep_map'])
    logger.debug("variation_map=%s" % variation_map)

    encoded_s_url = get_url_with_pkey(settings, source_url)
    logger.debug("encoded_s_url=%s" % encoded_s_url)
    runs_left = []

    for context in _create_variations(source_url, settings, variation_map):
        logger.debug("context=%s" % context)
        dest_url = _get_dest_url(settings, context['run_counter'])
        runs_left.append(context['run_counter'])
        encoded_d_url = smartconnector.get_url_with_pkey(settings,
            dest_url, is_relative_path=True, ip_address=settings['ip'])
        hrmcstages.copy_directories(encoded_s_url, encoded_d_url)

        for content_fname, content in _instantiate_context(
                source_url,
                settings,
                context).items():

            content_url = smartconnector.get_url_with_pkey(
                settings,
                os.path.join(dest_url, content_fname),
                is_relative_path=True, ip_address=settings['ip'])
            logger.debug("content_url=%s" % content_url)
            hrmcstages.put_file(content_url, content.encode('utf-8'))

        values_url = smartconnector.get_url_with_pkey(settings,
            os.path.join(dest_url, "values"),
            is_relative_path=True, ip_address=settings['ip'])
        hrmcstages.put_file(values_url, json.dumps(context))
    return runs_left


def _instantiate_context(source_url, settings, context):

    templ_pat = re.compile("(.*)_template")
    encoded_s_url = smartconnector.get_url_with_pkey(settings,
        source_url, is_relative_path=False)

    logger.debug("encoded_s_url=%s" % encoded_s_url)
    fnames = hrmcstages.list_dirs(encoded_s_url, list_files=True)

    logger.debug("fnames=%s" % fnames)
    new_content = {}
    for fname in fnames:
        logger.debug("fname=%s" % fname)
        templ_mat = templ_pat.match(fname)
        if templ_mat:
            base_fname = templ_mat.group(1)
            basename_url_with_pkey = smartconnector.get_url_with_pkey(
                settings,
                os.path.join(
                    source_url,
                    fname),
                is_relative_path=False)
            logger.debug("basename_url_with_pkey=%s" % basename_url_with_pkey)
            cont = hrmcstages.get_file(basename_url_with_pkey)
            t = Template(cont)
            con = Context(context)
            new_content[base_fname] = t.render(con)
    return new_content


def _get_dest_url(settings, run_counter):
    return "%s@%s" % (
            "nci",
            os.path.join(settings['payload_destination'],
                         str(settings['contextid']), str(run_counter)))


def _create_variations(url, settings, variation_map):
    values_map = {}
    try:
        encoded_val_url = get_url_with_pkey(
            settings,
            "%s/%s" % (url, "values"))
        logger.debug("values_file=%s" % encoded_val_url)
        values_content = hrmcstages.get_file(encoded_val_url)
    except IOError:
        logger.warn("no values file found")
    else:
        logger.debug("values_content = %s" % values_content)
        values_map = dict(json.loads(values_content))
    logger.debug("values_map=%s" % values_map)
    map_keys = variation_map.keys()
    map_ranges = [list(variation_map[x]) for x in map_keys]
    variations = []
    run_counter = 0
    for z in product(*map_ranges):
        context = dict(values_map)
        for i, k in enumerate(map_keys):
            context[k] = str(z[i])
        context['run_counter'] = run_counter
        run_counter += 1
        variations.append(context)
    return variations








