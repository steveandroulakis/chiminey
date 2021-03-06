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


import logging
import ast
import os
from chiminey.corestages.parent import Parent
from chiminey.smartconnectorscheduler.errors import BadSpecificationError
from chiminey.smartconnectorscheduler import jobs
from chiminey.runsettings import update, getval, SettingNotFoundException
from chiminey.storage import get_url_with_credentials, list_dirs


RMIT_SCHEMA = "http://rmit.edu.au/schemas"


logger = logging.getLogger(__name__)


class HRMCParent(Parent):
    """
        A list of corestages
    """

    def __init__(self, user_settings=None):
        logger.debug("HRMCParallelStage")
        pass

    def is_triggered(self, context):
        return False

    def __unicode__(self):
        return u"HRMCParallelStage"

    def get_run_map(self, settings, **kwargs):
        local_settings = settings.copy()
        run_settings = kwargs['run_settings']
        logger.debug('run_settings=%s' % run_settings)
        #fixme remove rand index
        try:
            rand_index = int(getval(run_settings, '%s/stages/run/rand_index' % RMIT_SCHEMA))
        except SettingNotFoundException:
            try:
                rand_index = int(getval(run_settings, '%s/input/hrmc/iseed' % RMIT_SCHEMA))
            except SettingNotFoundException, e:
                rand_index = 42
                logger.debug(e)
        update(local_settings, run_settings,
            '%s/input/hrmc/fanout_per_kept_result' % RMIT_SCHEMA,
            '%s/input/hrmc/optimisation_scheme' % RMIT_SCHEMA,
            '%s/input/hrmc/threshold' % RMIT_SCHEMA,
            '%s/input/hrmc/pottype' % RMIT_SCHEMA,
            '%s/system/max_seed_int' % RMIT_SCHEMA,
            '%s/system/random_numbers' % RMIT_SCHEMA,
            '%s/system/id' % RMIT_SCHEMA)

        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/input/hrmc/fanout_per_kept_result')
        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        # 'http://rmit.edu.au/schemas/input/hrmc/optimisation_scheme')
        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/input/hrmc/threshold')
        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/input/hrmc/pottype')
        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/system/max_seed_int')
        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/system/random_numbers')
        # smartconnectorscheduler.copy_settings(local_settings, run_settings,
        #     'http://rmit.edu.au/schemas/system/id')


        logger.debug("local_settings=%s" % local_settings)
        try:
            id = local_settings['id']
            #id = smartconnectorscheduler.get_existing_key(run_settings,
            #    'http://rmit.edu.au/schemas/system/misc/id')
        except KeyError, e:
            logger.error(e)
            id = 0
        logger.debug("id=%s" % id)
        # variations map spectification
        if 'pottype' in local_settings:
            logger.debug("pottype=%s" % local_settings['pottype'])
            try:
                pottype = int(local_settings['pottype'])
            except ValueError:
                logger.error("cannot convert %s to pottype" % local_settings['pottype'])
                pottype = 0
        else:
            pottype = 0

        optimisation_scheme = local_settings['optimisation_scheme']
        if optimisation_scheme == 'MC':
            N = local_settings['fanout_per_kept_result']
            rand_nums = jobs.generate_rands(local_settings,
                0, local_settings['max_seed_int'],
                N, rand_index)
            rand_index += N

            map = {
                'temp': [300],
                'iseed': rand_nums,
                'istart': [1 if id > 0 else 2],
                'pottype': [pottype]
            }
        elif optimisation_scheme == 'MCSA':
            threshold = local_settings['threshold']
            logger.debug("threshold=%s" % threshold)
            N = int(ast.literal_eval(threshold)[0])
            logger.debug("N=%s" % N)
            if not id:
                rand_nums = jobs.generate_rands(
                    local_settings,
                    0, local_settings['max_seed_int'],
                    4 * N, rand_index)
                rand_index += N
                map = {
                    'temp': [300],
                    'iseed': rand_nums,
                    'istart': [2],
                    'pottype': [pottype],
                }
            else:
                rand_nums = jobs.generate_rands(
                    local_settings,
                    0, local_settings['max_seed_int'],
                    1, rand_index)
                rand_index += N
                map = {
                    'temp': [i for i in [300, 700, 1100, 1500]],  # Fixme: temp should be hrmc parameter
                    'iseed': rand_nums,
                    'istart': [1],
                    'pottype': [pottype],
                }
        else:
            message = "Unknown dimensionality of problem"
            logger.error(message)
            raise BadSpecificationError(message)
        logger.debug('map=%s' % map)
        return map, rand_index

    #fixme: consider moving to parent class. do we need input dirs to calculate?
    def get_total_templates(self, maps, **kwargs):
        run_settings = kwargs['run_settings']
        output_storage_settings = kwargs['output_storage_settings']
        job_dir = kwargs['job_dir']
        try:
            id = int(getval(run_settings,
                                 '%s/system/id' % RMIT_SCHEMA))
        except (SettingNotFoundException, ValueError) as e:
            logger.debug(e)
            id = 0
        iter_inputdir = os.path.join(job_dir, "input_%s" % id)
        url_with_pkey = get_url_with_credentials(
            output_storage_settings,
            '%s://%s@%s' % (output_storage_settings['scheme'],
                           output_storage_settings['type'],
                            iter_inputdir),
            is_relative_path=False)
        logger.debug(url_with_pkey)
        input_dirs = list_dirs(url_with_pkey)
        for iter, template_map in enumerate(maps):
            logger.debug("template_map=%s" % template_map)
            map_keys = template_map.keys()
            logger.debug("map_keys %s" % map_keys)
            map_ranges = [list(template_map[x]) for x in map_keys]
            product = 1
            for i in map_ranges:
                product = product * len(i)
            total_templates = product * len(input_dirs)
            logger.debug("total_templates=%d" % (total_templates))
        return total_templates


