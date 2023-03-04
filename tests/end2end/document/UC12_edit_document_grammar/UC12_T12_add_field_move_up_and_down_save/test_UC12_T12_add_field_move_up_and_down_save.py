from seleniumbase import BaseCase

from tests.end2end.end2end_test_setup import End2EndTestSetup
from tests.end2end.helpers.screens.document_tree.screen_document_tree import (
    Screen_DocumentTree,
)
from tests.end2end.helpers.screens.document.form_edit_grammar import (
    Form_EditGrammar,
)
from tests.end2end.server import SDocTestServer


class Test_UC12_T12_AddFieldMoveUpAndDownSave(BaseCase):
    def test_01(self):
        test_setup = End2EndTestSetup(path_to_test_file=__file__)

        with SDocTestServer(
            input_path=test_setup.path_to_sandbox
        ) as test_server:
            self.open(test_server.get_host_and_port())

            screen_document_tree = Screen_DocumentTree(self)

            screen_document_tree.assert_on_screen()
            screen_document_tree.assert_contains_string("Document 1")

            screen_document = screen_document_tree.do_click_on_first_document()

            screen_document.assert_on_screen()
            screen_document.assert_is_document_title("Document 1")
            screen_document.assert_text("Hello world!")

            screen_document.assert_text("Requirement title")

            form_edit_grammar: Form_EditGrammar = (
                screen_document.do_open_edit_grammar_modal()
            )
            form_edit_grammar.assert_on_grammar()

            form_edit_grammar.do_add_field()
            form_edit_grammar.do_fill_in("", "CUSTOM_FIELD", -1)

            # Move 3 times up and two times down.
            form_edit_grammar.do_move_field_up()
            form_edit_grammar.do_move_field_up()
            form_edit_grammar.do_move_field_up()
            form_edit_grammar.do_move_field_down()
            form_edit_grammar.do_move_field_down()

            form_edit_grammar.do_form_submit()

        assert test_setup.compare_sandbox_and_expected_output()
