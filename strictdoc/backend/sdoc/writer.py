from enum import Enum
from typing import List, Optional

from strictdoc.backend.sdoc.models.anchor import Anchor
from strictdoc.backend.sdoc.models.document import Document
from strictdoc.backend.sdoc.models.document_config import DocumentConfig
from strictdoc.backend.sdoc.models.document_grammar import DocumentGrammar
from strictdoc.backend.sdoc.models.inline_link import InlineLink
from strictdoc.backend.sdoc.models.reference import (
    BibReference,
    ChildReqReference,
    FileReference,
    ParentReqReference,
    Reference,
)
from strictdoc.backend.sdoc.models.requirement import (
    CompositeRequirement,
    Requirement,
)
from strictdoc.backend.sdoc.models.section import FreeText, Section
from strictdoc.backend.sdoc.models.type_system import (
    GrammarElementFieldMultipleChoice,
    GrammarElementFieldReference,
    GrammarElementFieldSingleChoice,
    GrammarElementFieldString,
    GrammarElementFieldTag,
    RequirementFieldType,
)
from strictdoc.core.document_iterator import DocumentCachingIterator
from strictdoc.helpers.cast import assert_cast


class TAG(Enum):
    SECTION = 1
    REQUIREMENT = 2
    COMPOSITE_REQUIREMENT = 3


class SDWriter:
    def __init__(self):
        pass

    def write(self, document):
        document_iterator = DocumentCachingIterator(document)
        output = ""

        output += "[DOCUMENT]"
        output += "\n"

        output += "TITLE: "
        output += document.title
        output += "\n"

        document_config: DocumentConfig = document.config
        if document_config:
            uid = document_config.uid
            if uid:
                output += f"UID: {uid}"
                output += "\n"

            version = document_config.version
            if version:
                output += f"VERSION: {version}"
                output += "\n"

            classification = document_config.classification
            if classification is not None:
                output += f"CLASSIFICATION: {classification}"
                output += "\n"

            requirement_prefix = document_config.requirement_prefix
            if requirement_prefix is not None:
                output += f"REQ_PREFIX: {requirement_prefix}"
                output += "\n"

            markup = document_config.markup
            auto_levels_specified = document_config.ng_auto_levels_specified
            requirement_style = document_config.requirement_style
            requirement_in_toc = document_config.requirement_in_toc

            if (
                markup is not None
                or auto_levels_specified
                or requirement_style is not None
                or requirement_in_toc is not None
            ):
                output += "OPTIONS:"
                output += "\n"

                if markup is not None:
                    output += "  MARKUP: "
                    output += markup
                    output += "\n"

                if auto_levels_specified:
                    output += "  AUTO_LEVELS: "
                    output += "On" if document_config.auto_levels else "Off"
                    output += "\n"

                if requirement_style is not None:
                    output += "  REQUIREMENT_STYLE: "
                    output += requirement_style
                    output += "\n"

                if requirement_in_toc is not None:
                    output += "  REQUIREMENT_IN_TOC: "
                    output += requirement_in_toc
                    output += "\n"

        document_grammar: DocumentGrammar = document.grammar
        if not document_grammar.is_default:
            output += "\n[GRAMMAR]\n"
            output += "ELEMENTS:\n"
            for element in document_grammar.elements:
                output += "- TAG: "
                output += element.tag
                output += "\n  FIELDS:\n"
                refs_field: Optional[GrammarElementFieldReference] = None
                for grammar_field in element.fields:
                    if grammar_field.title == "REFS":
                        refs_field = assert_cast(
                            grammar_field, GrammarElementFieldReference
                        )
                        continue
                    output += SDWriter._print_grammar_field_type(grammar_field)

                relations: List = element.relations
                assert len(relations) > 0, relations

                # For backward compatibility, we print RELATIONS from REFS
                # grammar field if it exists.
                if not document_grammar.is_default and refs_field is not None:
                    relations = refs_field.convert_to_relations()
                output += "  RELATIONS:\n"

                assert len(relations) > 0, relations
                for element_relation in relations:
                    output += f"  - TYPE: {element_relation.relation_type}\n"
                    if element_relation.relation_role is not None:
                        output += (
                            f"    ROLE: {element_relation.relation_role}\n"
                        )

        for free_text in document.free_texts:
            output += "\n"
            output += self._print_free_text(free_text)
        closing_tags = []
        for content_node in document_iterator.all_content():
            while (
                len(closing_tags) > 0
                and content_node.ng_level <= closing_tags[-1][1]
            ):
                closing_tag, _ = closing_tags.pop()
                output += self._print_closing_tag(closing_tag)

            output += "\n"

            if isinstance(content_node, Section):
                output += self._print_section(content_node)
                closing_tags.append((TAG.SECTION, content_node.ng_level))
            elif isinstance(content_node, Requirement):
                if isinstance(content_node, CompositeRequirement):
                    output += "[COMPOSITE_"
                    output += content_node.requirement_type
                    output += "]\n"
                    closing_tags.append(
                        (TAG.COMPOSITE_REQUIREMENT, content_node.ng_level)
                    )
                else:
                    output += "["
                    output += content_node.requirement_type
                    output += "]\n"

                output += self._print_requirement_fields(
                    section_content=content_node, document=document
                )

        for closing_tag, _ in reversed(closing_tags):
            output += self._print_closing_tag(closing_tag)

        return output

    def _print_section(self, section: Section):
        assert isinstance(section, Section)
        output = ""
        output += "[SECTION]"
        output += "\n"

        if section.uid:
            output += "UID: "
            output += section.uid
            output += "\n"

        if section.custom_level:
            output += "LEVEL: "
            output += section.custom_level
            output += "\n"

        output += "TITLE: "
        output += str(section.title)
        output += "\n"
        if section.requirement_prefix is not None:
            output += "REQ_PREFIX: "
            output += section.requirement_prefix
            output += "\n"

        for free_text in section.free_texts:
            output += "\n"
            output += self._print_free_text(free_text)
        return output

    @staticmethod
    def _print_requirement_fields(
        section_content: Requirement, document: Document
    ):
        output = ""

        element = document.grammar.elements_by_type[
            section_content.requirement_type
        ]

        refs_already_printed = False
        for element_field in element.fields:
            field_name = element_field.title
            if field_name not in section_content.ordered_fields_lookup:
                continue
            fields = section_content.ordered_fields_lookup[field_name]
            for field in fields:
                if field.field_value_multiline is not None:
                    output += f"{field_name}: >>>"
                    output += "\n"
                    if len(field.field_value_multiline) > 0:
                        if field.field_value_multiline != "\n":
                            output += field.field_value_multiline
                        output += "\n"
                    output += "<<<"
                    output += "\n"
                elif field.field_value_references:
                    output += SDWriter._print_requirement_refs(
                        section_content, field
                    )
                    refs_already_printed = True
                elif field.field_value is not None:
                    if len(field.field_value) > 0:
                        output += f"{field_name}: "
                        output += field.field_value
                    else:
                        output += f"{field_name}:"
                    output += "\n"
                else:
                    output += f"{field_name}: "
                    output += "\n"

        if (
            not refs_already_printed
            and "REFS" in section_content.ordered_fields_lookup
        ):
            requirement_refs_fields = section_content.ordered_fields_lookup[
                "REFS"
            ]
            output += SDWriter._print_requirement_refs(
                section_content, requirement_refs_fields[0]
            )

        return output

    @staticmethod
    def _print_closing_tag(closing_tag):
        output = ""
        if closing_tag == TAG.SECTION:
            output += "\n"
            output += "[/SECTION]"
            output += "\n"
        if closing_tag == TAG.COMPOSITE_REQUIREMENT:
            output += "\n"
            output += "[/COMPOSITE_REQUIREMENT]"
            output += "\n"
        return output

    @staticmethod
    def _print_free_text(free_text):
        assert isinstance(free_text, FreeText)
        output = ""
        output += "[FREETEXT]"
        output += "\n"
        output += SDWriter.print_free_text_content(free_text)
        if output[-1] != "\n":
            output += "\n"
        output += "[/FREETEXT]"
        output += "\n"
        return output

    @staticmethod
    def _print_grammar_field_type(grammar_field):
        output = ""
        output += "  - TITLE: "
        output += grammar_field.title
        output += "\n"
        output += "    TYPE: "

        if isinstance(grammar_field, GrammarElementFieldString):
            output += RequirementFieldType.STRING
        elif isinstance(grammar_field, GrammarElementFieldSingleChoice):
            output += RequirementFieldType.SINGLE_CHOICE
            output += "("
            output += ", ".join(grammar_field.options)
            output += ")"
        elif isinstance(grammar_field, GrammarElementFieldMultipleChoice):
            output += RequirementFieldType.MULTIPLE_CHOICE
            output += "("
            output += ", ".join(grammar_field.options)
            output += ")"
        elif isinstance(grammar_field, GrammarElementFieldTag):
            output += RequirementFieldType.TAG
        elif isinstance(grammar_field, GrammarElementFieldReference):
            output += RequirementFieldType.REFERENCE
            output += "("
            output += ", ".join(grammar_field.types)
            output += ")"
        else:
            raise NotImplementedError from None

        output += "\n"
        output += "    REQUIRED: "
        output += "True" if grammar_field.required else "False"
        output += "\n"
        return output

    @staticmethod
    def print_free_text_content(free_text):
        assert isinstance(free_text, FreeText)
        output = ""

        for _, part in enumerate(free_text.parts):
            if isinstance(part, str):
                output += part
            elif isinstance(part, InlineLink):
                output += "[LINK: "
                output += part.link
                output += "]"
            elif isinstance(part, Anchor):
                output += "[ANCHOR: "
                output += part.value
                if part.has_title:
                    output += ", "
                    output += part.title
                output += "]"
                output += "\n"
            else:
                raise NotImplementedError(part)
        return output

    @classmethod
    def _print_requirement_refs(cls, requirement: Requirement, field):
        output = ""
        if (
            requirement.ng_document_reference is not None
            and requirement.document.ng_at_least_one_relations_field
        ) or not requirement.ng_uses_old_refs_field:
            output += "RELATIONS:"
        else:
            output += "REFS:"
        output += "\n"

        reference: Reference
        for reference in field.field_value_references:
            output += "- TYPE: "
            output += reference.ref_type
            output += "\n"

            if isinstance(reference, BibReference):
                ref: BibReference = reference
                output += "  FORMAT: "
                output += ref.bib_entry.bib_format
                output += "\n"
                output += "  VALUE: "
                output += ref.bib_entry.bib_value
                output += "\n"
            elif isinstance(reference, FileReference):
                ref: FileReference = reference
                file_format = ref.get_file_format()
                if file_format:
                    output += "  FORMAT: "
                    output += file_format
                    output += "\n"
                output += "  VALUE: "
                output += ref.get_posix_path()
                output += "\n"
            elif isinstance(reference, ParentReqReference):
                parent_reference: ParentReqReference = reference
                output += "  VALUE: "
                output += parent_reference.ref_uid
                output += "\n"
                if parent_reference.role is not None:
                    output += "  ROLE: "
                    output += parent_reference.role
                    output += "\n"
            elif isinstance(reference, ChildReqReference):
                child_reference: ChildReqReference = reference
                output += "  VALUE: "
                output += child_reference.ref_uid
                output += "\n"
                if child_reference.role is not None:
                    output += "  ROLE: "
                    output += child_reference.role
                    output += "\n"
            else:
                raise AssertionError("Must not reach here.")
        return output
