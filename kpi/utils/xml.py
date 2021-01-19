# coding: utf-8
from lxml import etree


def strip_nodes(
    source: str,
    nodes_to_keep: list,
    use_xpath: bool = False,
    xml_declaration: bool = False,
) -> str:
    """
    Returns an stripped version of `source`. It keeps only nodes provided in
    `nodes_to_keep`
    """
    if len(nodes_to_keep) == 0:
        return source

    # Build xml to be parsed
    xml_doc = etree.fromstring(source)
    tree = etree.ElementTree(xml_doc)
    root_element = tree.getroot()
    root_path = tree.getpath(root_element)

    def get_xpath_matches():
        if use_xpath:
            xpaths_ = []
            for xpath_ in nodes_to_keep:
                leading_slash = '' if xpath_.startswith('/') else '/'
                trailing_slash = '' if xpath_.endswith('/') else '/'
                xpaths_.append(f'{leading_slash}{xpath_}{trailing_slash}')
            return xpaths_

        xpath_matches = []
        # Retrieve XPaths of all nodes we need to keep
        for node_to_keep in nodes_to_keep:
            for node in tree.iter(node_to_keep):
                xpath_match = remove_root_path(tree.getpath(node))
                # To make a difference between XPaths with same beginning
                # string, we need to add a trailing slash for later comparison
                # in `process_node()`.
                # For example, `subgroup1` and `subgroup11` both start with
                # `subgroup1` but `subgroup11/` and `subgroup1/` do not.
                xpath_matches.append(f'{xpath_match}/')

        return xpath_matches

    def process_node(node_: etree._Element, xpath_matches_: list):
        """
        `process_node()` is a recursive function.

        First, it loops through all children of the root element.
        Then for each child, it loops through its children if any, etc...
        When all children are processed, it checks whether the node should be
        removed or not.

        The most nested children are processed first in order to know which
        parents must be kept.

        For example:
        With `subset_fields = ['question_2', 'question_3']` and this XML:
        <root>
          <group>
              <question_1>Value1</question_1>
              <question_2>Value2</question_2>
          </group>
          <question_3>Value3</question_3>
        </root>

         Nodes are processed in this order:
         - `<question_1>`: Removed because not in `subset_field`

         - `<question_2>`: Kept. Parent node `<group>` is tagged `do_not_delete`  # noqa

         - `<group>`: Kept even if it is not in `subset_field` because
                      it is tagged `do_not_delete` by its child `<question_2>`

         - `<question_3>`: Kept.

        Results:
        <root>
          <group>
              <question_2>Value2</question1>
          </group>
          <question3>Value3</question3>
        </root>
        """
        for child in node_.getchildren():
            process_node(child, xpath_matches_)

        # Get XPath of current node
        node_xpath = remove_root_path(tree.getpath(node_))

        # If `node_path` does not start with one of the occurrences previously
        # found, it must be removed.
        if (
            not f'{node_xpath}/'.startswith(tuple(xpath_matches_))
            and node_.get('do_not_delete') != 'true'
        ):
            if node_ != root_element:
                node_.getparent().remove(node_)
        elif node_xpath != '':
            # node matches, keep its parent too.
            node_.getparent().set('do_not_delete', 'true')

        # All children have been processed and `node_` seems to be a parent we
        # need to keep. Remove `do_not_delete` flag to avoid rendering it in
        # final xml
        if node_.attrib.get('do_not_delete'):
            del node_.attrib['do_not_delete']

    def remove_root_path(path_: str) -> str:
        return path_.replace(root_path, '')

    xpath_matches = get_xpath_matches()
    process_node(root_element, xpath_matches)

    return etree.tostring(
        tree,
        pretty_print=True,
        encoding='utf-8',
        xml_declaration=xml_declaration,
    ).decode()
