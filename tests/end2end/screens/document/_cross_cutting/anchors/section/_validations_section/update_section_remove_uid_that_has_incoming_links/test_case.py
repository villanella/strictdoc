from tests.end2end.e2e_case import E2ECase
from tests.end2end.end2end_test_setup import End2EndTestSetup
from tests.end2end.helpers.screens.document.form_edit_section import (
    Form_EditSection,
)
from tests.end2end.helpers.screens.project_index.screen_project_index import (
    Screen_ProjectIndex,
)
from tests.end2end.server import SDocTestServer


class Test(E2ECase):
    def test(self):
        test_setup = End2EndTestSetup(path_to_test_file=__file__)

        with SDocTestServer(
            input_path=test_setup.path_to_sandbox
        ) as test_server:
            self.open(test_server.get_host_and_port())

            screen_project_index = Screen_ProjectIndex(self)

            screen_project_index.assert_on_screen()
            screen_project_index.assert_contains_document("Document 1")

            screen_document = screen_project_index.do_click_on_first_document()

            screen_document.assert_on_screen_document()
            screen_document.assert_header_document_title("Document 1")

            screen_document.assert_text("Hello world!")

            section = screen_document.get_section()
            form_edit_section: Form_EditSection = (
                section.do_open_form_edit_section()
            )
            form_edit_section.do_clear_field("section_uid")
            form_edit_section.do_form_submit_and_catch_error(
                "Cannot remove a section UID 'Section-UID' because there are "
                "existing LINKs referencing this section. The incoming links "
                "are located in these nodes: "
                "'Second section', 'Third section'."
            )

        assert test_setup.compare_sandbox_and_expected_output()
