import os

from tests.end2end.e2e_case import E2ECase
from tests.end2end.helpers.screens.project_index.screen_project_index import (
    Screen_ProjectIndex,
)
from tests.end2end.server import SDocTestServer

path_to_this_test_file_folder = os.path.dirname(os.path.abspath(__file__))


class Test_ProjectOptions_Features_01_OptionSpecified(E2ECase):
    def test(self):
        with SDocTestServer(
            input_path=path_to_this_test_file_folder
        ) as test_server:
            self.open(test_server.get_host_and_port())

            screen_project_index = Screen_ProjectIndex(self)
            screen_project_index.assert_on_screen()

            # TODO: Add more assertions indicating that ALL features are
            # activated.
            screen_project_index.assert_link_to_requirements_coverage_present()
            screen_project_index.assert_link_to_source_coverage_present()

            screen_project_index.assert_no_js_and_404_errors()
