import pytest
from taf import logging
from taf.af_support_tools import IssueID, Config
from taf.text import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
c = Config()


@pytest.mark.example
@IssueID('ESTS-140402')
def test_sample_read_config_file_pass():
    """
    This sample test is designed to demonstrate a data driven test by reading properties from a configuration file.
    While demonstrating the list compare function a mocked API call is used to provide sample json data.
    This test is designed to pass.
    """

    # Get attributes
    widget_attributes_list = c.get_option('widget_class_1', 'attributes')
    widget_attributes_list = widget_attributes_list.split(',')

    # Mock call to API to retrieve data
    mock_data_attributes_list = ['description', 'model_number', 'name', 'serial_number', 'uid',
                                 'class_1_only_attribute']

    # Sample 'assert'
    pass_flag = List(widget_attributes_list).all_items_in(mock_data_attributes_list)
    assert pass_flag == True


@pytest.mark.parametrize('my_var', [
    pytest.param('A', marks=IssueID('ESTS-140404')),
    pytest.param('B', marks=IssueID('ESTS-140405')),
    pytest.param('C', marks=IssueID('ESTS-140406')),
    pytest.param('D', marks=IssueID('ESTS-140407')),
    pytest.param('Bad Data', marks=IssueID('ESTS-140408')),
])
def test_sample_parametrize_vars(my_var):
    """
    This sample test is designed to demonstrate how to parametrizes a single test which will result in producing multiple tests being reported, one for each parameter passed.
    This test is designed to pass, fail and skip demonstrating how parametrized data changes that tests results.
    """
    # Loop through each parametrized variable checking for data equal to C or Bad Data
    logger.info('Testing %s' % my_var)
    if my_var == 'C':
        pytest.skip('I don\'t like the letter C so please skip')
