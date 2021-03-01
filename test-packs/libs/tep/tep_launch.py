import shutil
import time
import os
import urllib.request
import tempfile

from libs.pyjubula import *
from libs.pyjubula.component import CAPError
import libs.tep.tep_classes as tc

config(log_level=LOG_ERROR)


class TEPLauncher:
    host = None
    jre_params, aut_params, jre_binary, working_dir, class_path = (None,) * 5
    threshold, name_factor, path_factor, context_factor = 1.0, 1.0, 1.0, 1.0
    aut_id = 'TEP'

    agent = None
    tep_source_dir = None

    def __init__(self, jubula_agent='localhost:60000', host_teps='WALDEVITMZQA03', classes_dir=None,
                 username='sysadmin', password='', need_download=True):
        self.aut = None
        self.classes_dir = classes_dir
        if 'rocketsoftware' in host_teps.lower():
            self.host_teps = host_teps
        else:
            self.host_teps = host_teps + '.dev.rocketsoftware.com'

        if 'rocketsoftware' in jubula_agent.lower():
            self.jubula_agent = jubula_agent
        else:
            h, p = jubula_agent.split(':')
            self.jubula_agent = f'{h}:{p}'
        self.username = username
        self.password = password
        self.need_download = need_download
        self.tep_launch()

    def download(self):
        if not self.need_download:
            return

        if self.classes_dir is not None:
            target_dir = self.classes_dir + '/classes'
            shutil.rmtree(self.classes_dir + '/classes')
        else:
            self.tep_source_dir = tempfile.TemporaryDirectory()
            target_dir = self.tep_source_dir.name + '/classes'

        os.mkdir(target_dir)

        base_url = 'http://'+self.host_teps+':15200/'

        for i in tc.classes:
            urllib.request.urlretrieve(base_url+i, os.path.join(target_dir, i))
        self.classes_dir = target_dir

    def start(self):
        if self.agent is None:
            self.agent = AUTAgent()
            self.agent.connect(self.jubula_agent)

        jre_params = '-Djnlp.kjr.trace.mode=LOCAL -Djnlp.kjr.trace.params=ERROR -Djnlp.ORBtcpNoDelay=true ' \
                    '-Djnlp.ibm.stream.nio=true -Djnlp.cnp.http.url.host=WALDEVITMZQA03.dev.rocketsoftware.com ' \
                    '-Djnlp.vbroker.agent.enableLocator=false -Djnlp.org.omg.CORBA.ORBClass=com.inprise.vbroker.orb.ORB ' \
                    '-Djnlp.org.omg.CORBA.ORBSingletonClass=com.inprise.vbroker.orb.ORBSingleton'.format(self.host_teps)

        aut_params = '-showversion -noverify'
        # jre_binary = 'C:/Program Files (x86)/Common Files/Oracle/Java/javapath/javaw.exe'
       # jre_binary = 'C:/Program Files/Java/jre/bin/javaw.exe'
        jre_binary = 'C:/Program Files/Java/jre1.8.0_281/bin/javaw.exe'
        #jre_binary = 'C:/IBMJAVA71/jre/bin/javaw.exe'
        working_dir = 'C:/AUT_WD/'
        dir_prefix = ';' + self.classes_dir + '/'

        class_path = dir_prefix + dir_prefix.join(tc.classes)

        if self.aut_id in self.agent.aut_list:
            return
        #self.agent.start_aut(aut_id=self.aut_id, jre_params=jre_params, aut_params=aut_params, jre_binary=jre_binary,
         #                    class_name='candle.fw.pres.CMWApplet', working_dir=working_dir, class_path=class_path)

    def logon(self):
        self.aut = self.agent.aut_connect(self.aut_id)
        self.aut.define()
        logon_mapping = ['javax.swing.text.JTextComponent',
                         'candle.kjr.swing.FixedLengthTextField',
                         ['frame0', 'javax.swing.JDialog_1', 'javax.swing.JRootPane_1', 'null.layeredPane', 'null.contentPane', 'javax.swing.JPanel_1',
                          'javax.swing.JPanel_2', 'candle.kjr.swing.ImagePanel_1', 'javax.swing.JPanel_1', 'candle.kjr.swing.FixedLengthTextField_1'],
                         ['javax.swing.JLabel_1', 'javax.swing.JLabel_2', 'javax.swing.JLabel_3', 'javax.swing.JLabel_4', 'javax.swing.JPasswordField_1']]

        password_mapping = ["javax.swing.text.JTextComponent",
                            "javax.swing.JPasswordField",
                            ["frame0", "javax.swing.JDialog_1", "javax.swing.JRootPane_1", "null.layeredPane", "null.contentPane", "javax.swing.JPanel_1",
                             "javax.swing.JPanel_2", "candle.kjr.swing.ImagePanel_1", "javax.swing.JPanel_1", "javax.swing.JPasswordField_1"],
                            ["candle.kjr.swing.FixedLengthTextField_1", "javax.swing.JLabel_1", "javax.swing.JLabel_2",
                             "javax.swing.JLabel_3", "javax.swing.JLabel_4"]]

        ok_button_mapping = ['javax.swing.AbstractButton',
                             'javax.swing.JButton',
                             ['frame0', 'javax.swing.JDialog_1', 'javax.swing.JRootPane_1', 'null.layeredPane', 'null.contentPane', 'javax.swing.JPanel_1',
                              'javax.swing.JPanel_1', 'javax.swing.JButton_1'],
                             ['javax.swing.JButton_1', 'javax.swing.JButton_2']]
        tree_mapping = ['javax.swing.JTree',
                        'candle.fw.pres.adapters.TreeAdapter$ToolTipTree',
                        ['frame2', 'javax.swing.JRootPane_1', 'null.layeredPane', 'null.contentPane', 'javax.swing.JPanel_1',
                         'candle.kjr.swing.ui.TivoliSplitPane_1', 'javax.swing.JPanel_1', 'candle.kjr.swing.ui.TivoliSplitPane_1',
                         'javax.swing.JPanel_2', 'javax.swing.JPanel_1', 'candle.fw.pres.Navigator$NavigatorTabbedPane_1',
                         'javax.swing.JPanel_1', 'javax.swing.JScrollPane_1', 'javax.swing.JViewport_1',
                         'candle.fw.pres.adapters.TreeAdapter$ToolTipTree_1'],
                        []]
        #logon_field = TextComponent('logon field', logon_mapping, self.aut)
       # password_field = TextComponent('Password field', password_mapping, self.aut)
        #ok_button = ButtonComponent('OK button', ok_button_mapping, self.aut)
        tep_tree = TreeComponent("Navigator", tree_mapping, self.aut)

        #logon_field.wait_for(20000, 5000)
        #logon_field.text(self.username)
        #if self.password != '':
        #    password_field.text(self.password)
        #ok_button.click()
        #ok_button.click()
        tep_tree.wait_for(60000, 1000)

    def tep_launch(self):
        self.download()
        self.start()
        self.logon()

    def logoff(self):
        if self.aut_id in self.agent.aut_list:
            self.agent.stop_aut(aut_id=self.aut_id)
            time.sleep(5)

    @property
    def tep_tree(self):
        tree_mapping = ['javax.swing.JTree',
                        'candle.fw.pres.adapters.TreeAdapter$ToolTipTree',
                        ['frame2', 'javax.swing.JRootPane_1', 'null.layeredPane', 'null.contentPane',
                         'javax.swing.JPanel_1',
                         'candle.kjr.swing.ui.TivoliSplitPane_1', 'javax.swing.JPanel_1',
                         'candle.kjr.swing.ui.TivoliSplitPane_1',
                         'javax.swing.JPanel_2', 'javax.swing.JPanel_1',
                         'candle.fw.pres.Navigator$NavigatorTabbedPane_1',
                         'javax.swing.JPanel_1', 'javax.swing.JScrollPane_1', 'javax.swing.JViewport_1',
                         'candle.fw.pres.adapters.TreeAdapter$ToolTipTree_1'],
                        []]
        exp_tree_mapping = ["javax.swing.JTree",
                            "candle.fw.pres.adapters.TreeAdapter$ToolTipTree",
                            ["frame2", "javax.swing.JRootPane_1", "null.layeredPane", "null.contentPane",
                             "javax.swing.JPanel_1",
                             "candle.kjr.swing.ui.TivoliSplitPane_1", "javax.swing.JPanel_2", "javax.swing.JPanel_1",
                             "candle.fw.pres.Navigator$NavigatorTabbedPane_1", "javax.swing.JPanel_1",
                             "javax.swing.JScrollPane_1",
                             "javax.swing.JViewport_1", "candle.fw.pres.adapters.TreeAdapter$ToolTipTree_1"],
                            []]
        add_tree_mapping = ["javax.swing.JTree",
                            "candle.fw.pres.adapters.TreeAdapter$ToolTipTree",
                            ["frame2", "javax.swing.JRootPane_1", "null.layeredPane", "null.contentPane",
                             "javax.swing.JPanel_1",
                             "candle.kjr.swing.ui.TivoliSplitPane_1", "javax.swing.JPanel_2",
                             "candle.kjr.swing.ui.TivoliSplitPane_1", "javax.swing.JPanel_2",
                             "javax.swing.JPanel_1", "candle.fw.pres.Navigator$NavigatorTabbedPane_1",
                             "javax.swing.JPanel_1", "javax.swing.JScrollPane_1",
                             "javax.swing.JViewport_1", "candle.fw.pres.adapters.TreeAdapter$ToolTipTree_1"],
                            []]
        add_tree_mapping2 = ["javax.swing.JTree",
                             "candle.fw.pres.adapters.TreeAdapter$ToolTipTree",
                             ["frame2", "javax.swing.JRootPane_1", "null.layeredPane", "null.contentPane",
                              "javax.swing.JPanel_1",
                              "candle.kjr.swing.ui.TivoliSplitPane_1", "javax.swing.JPanel_1",
                              "candle.kjr.swing.ui.TivoliSplitPane_1", "javax.swing.JPanel_2",
                              "javax.swing.JPanel_1", "candle.fw.pres.Navigator$NavigatorTabbedPane_1",
                              "javax.swing.JPanel_1", "javax.swing.JScrollPane_1",
                              "javax.swing.JViewport_1", "candle.fw.pres.adapters.TreeAdapter$ToolTipTree_1"],
                             []]
        tep_tree = TreeComponent("Navigator", tree_mapping, self.aut)
        exp_tep_tree = TreeComponent("Navigator", exp_tree_mapping, self.aut)
        add_tep_tree = TreeComponent('Navigator', add_tree_mapping, self.aut)
        add_tep_tree2 = TreeComponent('Navigator', add_tree_mapping2, self.aut)
        try:
            tep_tree.wait_for(10, 0)
        except CAPError:
            pass
        else:
            return tep_tree
        try:
            exp_tep_tree.wait_for(10, 0)
        except CAPError:
            pass
        else:
            return exp_tep_tree
        try:
            add_tep_tree.wait_for(10, 0)
        except CAPError:
            pass
        else:
            return add_tep_tree
        try:
            add_tep_tree2.wait_for(10, 0)
        except CAPError:
            raise Exception('Not able to locate the navigator tree')
        else:
            return add_tep_tree2
