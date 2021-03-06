# Copyright (C) 2014, RMIT University

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

from chiminey.corestages.strategies.strategy import Strategy
from chiminey import messages

class ClusterStrategy(Strategy):
    def create_resource(self, local_settings):
        group_id = 'UNKNOWN'
        created_nodes = []
        created_nodes.append(['1', local_settings['ip_address'], 'unix', 'running'])
        messages.info_context(local_settings['contextid'], "1: create (%s nodes created)" % len(created_nodes))
        return group_id, created_nodes

    def complete_bootstrap(self, bootstrap_class, local_settings):
        bootstrap_class.bootstrapped_nodes.append(['1', local_settings['ip_address'], 'unix', 'running'])


    def complete_schedule(self, schedule_class, local_settings):
        schedule_class.total_scheduled_procs = 1
        schedule_class.scheduled_nodes.append(['1', local_settings['ip_address'], 'unix', 'running'])
        schedule_class.all_processes.append({'status': 'ready', 'retry_left': '2',
                                             'ip_address': local_settings['ip_address'], 'id': '1'})#fixme: process id assumes single iteration
        schedule_class.current_processes.append({'status': 'ready', 'retry_left': '2',
                                             'ip_address': local_settings['ip_address'], 'id': '1'})
