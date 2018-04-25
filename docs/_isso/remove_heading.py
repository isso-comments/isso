
from docutils import nodes
from sphinx.writers.html import HTMLTranslator


class IssoTranslator(HTMLTranslator):

    def visit_title(self, node):
        if self.section_level == 1:
            raise nodes.SkipNode
        HTMLTranslator.visit_title(self, node)
