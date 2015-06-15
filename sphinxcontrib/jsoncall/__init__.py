import docutils, json, os
from urlparse import urljoin, urlsplit
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst import Directive
from itertools import chain, takewhile
from ._escaping import escape

JSONCALL_JS = """
<script>

function getPrintObject(object)
{
    return JSON.stringify(object);
}

function indented_fill_%(callid)s_result(data) {
    if (typeof data !== "string")
        data = JSON.stringify(data, undefined, 2);
    var dest = jQuery("#jsoncall_%(callid)s_result");
    dest.html(jsoncall_syntax_highlight(data));
}

function toogle(key) {
    obj = jQuery('#' + key);
    if (obj.prop('disabled')) {
        obj.removeAttr('disabled');
    } else {
        obj.attr('disabled', 'disabled');
    }
}

function cast_number(val) {
    intval = parseInt(val, 10);
    if (val == intval) return intval;
    return val;
}

function get_%(callid)s_params() {
    var params = {};
    jQuery("#jsoncall_%(callid)s_params input").each(function(i, e) {
        e = jQuery(e);
        if (!e.prop('disabled')) {
            params[e.attr("name")] = e.val();
        }
    });
    jQuery("#jsoncall_%(callid)s_params select").each(function(i, e) {
        e = jQuery(e);
        value = $('#'+e.attr("id")+' option:selected').val();
        if (!e.prop('disabled')) {
            params[e.attr("name")] = value;
        }
    });
    return params;
}

function show_%(callid)s_call() {
    params = get_%(callid)s_params();
    var dest = jQuery("#jsoncall_%(callid)s_result");
    dest.html(jsoncall_syntax_highlight(getPrintObject(params)));
}

function perform_%(callid)s_call() {
    params = get_%(callid)s_params();

    jQuery.ajax({
                "url":"%(url)s",
                "type": "%(http_method)s",
                "data": params,
                "dataType":"json",
                'success':function(data, textStatus, jqXHR) {
                       indented_fill_%(callid)s_result(data);
                },
                'error':function(jqXHR, textStatus, errorThrown) {
                        var dest = jQuery("#jsoncall_%(callid)s_result");
                        if (textStatus === "error")
                            dest.text(jqXHR.statusText);
                        else
                            dest.text(textStatus);
                }
    });
}
</script>
"""

class jsoncall(nodes.Element):
    def __init__(self, url, http_method, params, callid, static_response):
        super(jsoncall, self).__init__()
        self.http_method = http_method
        self.url = url
        self.params = params
        self.callid = callid
        self.static_response = static_response

def visit_jsoncall_html(self, node):
    self.body.append(JSONCALL_JS % dict(callid=node.callid, url=node.url, http_method=node.http_method))
 
def get_real_key(key):
    if key.startswith("option:"):
        return key[len("option:"):]
    return key

def depart_jsoncall_html(self, node):
    self.body.append('<table class="jsoncall_testform" id="jsoncall_%s_params">' % node.callid)
    if isinstance(node.params, dict):
        items = node.params.items()
    else:
        items = node.params

    for next_item in items:
        optional = False
        key, value = next_item[:2]
        extras = ''
        disabled = ''
        self.body.append('<tr>')
        real_key = get_real_key(key)
        field_id = "f_%s_%s" % (real_key, node.callid)
        if len(next_item) >= 3:
            if "optional" in next_item[2]:
                extras += 'onclick="toogle(\'%s\')" ' % field_id
            if "disabled" in next_item[2]:
                disabled = 'disabled="disabled" '
        self.body.append('<td %s> %s </td>' % (extras, real_key))
        if key.startswith("option:"):
            options = "".join(map(lambda (desc, value): "<option value='%s'>%s</option>" % (value, escape(desc)), value))
            self.body.append('<td><select name="%s" id="%s" %s>%s</select></td>' % (real_key, field_id, disabled, options))
        else:
            value = escape(value)
            self.body.append('<td><input style="min-width:200px;padding:5px;" type="text" name="%s" id="%s" %s value="%s"/></td>' %
                    (real_key, field_id, disabled, value))
        self.body.append('</tr>')
    self.body.append('</table>')

    self.body.append('<div class="jsoncall_button" onclick="show_%s_call()">Show Request</div> &nbsp;' % node.callid)
    self.body.append('<div class="jsoncall_button" id="jsoncall_%s_button" onclick="perform_%s_call()">Test Call</div>' % (node.callid, node.callid))
    self.body.append('<pre class="jsoncall_result" id="jsoncall_%s_result">%s</pre>' % (node.callid, node.static_response))
    self.body.append("""
<script>
    var res = jQuery("#jsoncall_%(callid)s_result");
    res.html(indented_fill_%(callid)s_result(res.text()));
</script>""" % {'callid': node.callid})

class JSONCall(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = True
    option_spec = {
                    'method': directives.unchanged,
                    'port': directives.nonnegative_int
                }

    def run(self):
        env = self.state.document.settings.env

        http_method = self.options.get('method', 'GET')
        http_port = self.options.get('port', '')
        base_url = env.config.jsoncall_baseurl
        url = self.arguments[0]
        if http_port:
            split_res = urlsplit(base_url)
            if ':' in split_res.netloc:
                netloc = ":".join(split_res.netloc.split(':')[:-1]) # just strip port if it already exists
            else:
                netloc = split_res.netloc + ":" + str(http_port)
            base_url = split_res._replace(netloc=netloc).geturl()
            #raise RuntimeError(base_url)
        apiurl = urljoin(base_url, url)

        iter_content = chain(self.content)
        content = '\n'.join(list(takewhile(lambda x: x.strip(), iter_content)))
        static_response = '\n'.join(list(iter_content))
        callid = env.new_serialno('jsoncall')
        try:
            params = json.loads(content)
        except ValueError, v:
            raise ValueError("Invalid json: %s\nError: %s" % (content, v))
        return [jsoncall(url=apiurl, http_method=http_method, params=params,
                         callid=callid, static_response=static_response)]

def on_init(app):
    dirpath = os.path.dirname(__file__)
    static_path = os.path.join(dirpath, '_static')
    app.config.html_static_path.append(static_path)

    if app.config.jsoncall_inject_css:
	app.add_stylesheet('jsoncall.css')

    app.add_javascript('jsoncall.js')


def setup(app):
    app.add_config_value('jsoncall_inject_css', True, 'env')
    app.add_config_value('jsoncall_baseurl', '', 'html')

    app.connect('builder-inited', on_init)
    app.add_node(jsoncall, html=(visit_jsoncall_html, depart_jsoncall_html))
    app.add_directive('jsoncall', JSONCall)

