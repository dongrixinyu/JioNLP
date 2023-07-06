# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP


from jionlp.util.funcs import absence


# ---------------------------------------------------------------------
# HTML 格式文档正则
SCRIPT_TAG_PATTERN = '(<script(.|\n)*?>(.|\n)*?</script>|<SCRIPT(.|\n)*?>(.|\n)*?</SCRIPT>)'
STYLE_TAG_PATTERN = '(<style(.|\n)*?>(.|\n)*?</style>|<STYLE(.|\n)*?>(.|\n)*?</STYLE>)'
TABLE_TAG_PATTERN = '(<table(.|\n)*?>(.|\n)*?</table>|<TABLE(.|\n)*?>(.|\n)*?</TABLE>)'
ORDERED_LIST_TAG_PATTERN = '(<ol(.|\n)*?>(.|\n)*?</ol>|<OL(.|\n)*?>(.|\n)*?</OL>)'
UNORDERED_LIST_TAG_PATTERN = '(<ul(.|\n)*?>(.|\n)*?</ul>|<UL(.|\n)*?>(.|\n)*?</UL>)'
FOOTER_TAG_PATTERN = '(<footer(.|\n)*?>(.|\n)*?</footer>|<FOOTER(.|\n)*?>(.|\n)*?</FOOTER>)'
NAVIGATION_TAG_PATTERN = '(<nav(.|\n)*?>(.|\n)*?</nav>|<NAV(.|\n)*?>(.|\n)*?</NAV>)'

META_TAG_PATTERN = '<meta.*?>'
COMMENT_TAG_PATTERN = '<!--(.|\n)*?-->'
BREAK_LINE_TAG_PATTERN = '(<br>|<BR>)'


HTML_TAG_STRICT_PATTERN = \
    '(<([a-z]{1,8}|[A-Z]{1,8}|h[1-6]|!DOCTYPE|\?xml)([ \n]((.|\n)+?))?>|' \
    '</([a-z]{1,8}|[A-Z]{1,8}|h[1-6])>|' \
    '<![endif]-->)'

HTML_TAG_PATTERN = '<(.|\n)*?>'

ADD_NEW_LINE_PATTERN = r'(</p>|</h1>|</h2>|</h3>|</h4>|</h5>)'


# ---------------------------------------------------------------------
# 属性正则
NAME_ATTR_PATTERN = '(name="([^"]*)"|name=\'([^\']*)\')'
CONTENT_ATTR_PATTERN = '(content="([^"]*)"|content=\'([^\']*)\')'

# ---------------------------------------------------------------------
# 冗余空格正则
TAB_NEW_LINE_PATTERN = '[\n\t ]{1,}\n[\n\t ]{1,}'
