import re
import time
from libs.pyjubula.component import CAPError

from libs.tep.tep_launch import TEPLauncher


class TEP(TEPLauncher):
    # agent, aut, sys, tems, mappings = (None,) * 5

    def __init__(self, jubula_agent, host_teps, classes_dir=None, username='sysadmin', password='',
                 sys='RSD4', plex='RSPLEXL4', need_download=False):
        self.sys = sys
        self.plex = plex
        super().__init__(jubula_agent, host_teps, classes_dir, username, password, need_download)

    def navigate_to_node(self, node_path):
        # for ivt, we have additional level because of OM for z/OS
        ivt_plex = f'/<html>{self.plex}:MVS:SYSPLEX<\/html>'

        tep_path = f'<html>Enterprise<\/html>/<html>z\/OS Systems<\/html>{ivt_plex}/<html>' + self.sys + '<\/html>'
        for node in node_path:
            tep_path += f'/<html>{node}<\/html>'

        current_tree = self.tep_tree
        try:
            current_node = re.findall('(?<=<html>).*(?=</html>)', current_tree.selected_node())[0]
        except CAPError:
            current_node = None
        #finally:
        #    if current_node in node_path:
        #        current_tree.select_node_by_text('<html>Enterprise<\/html>')
        current_tree = self.tep_tree
        current_tree.select_node_by_text(tep_path)
        time.sleep(10)
        return current_tree


