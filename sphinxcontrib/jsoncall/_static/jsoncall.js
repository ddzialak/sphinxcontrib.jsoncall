
function jsoncall_syntax_highlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'jsoncall_sxh_number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'jsoncall_sxh_key';
            } else {
                cls = 'jsoncall_sxh_string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'jsoncall_sxh_boolean';
        } else if (/null/.test(match)) {
            cls = 'jsoncall_sxh_null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

function obj_to_json(object)
{
    return JSON.stringify(object);
}

function toogle(key) {
    obj = jQuery('#' + key);
    if (obj.prop('disabled')) {
        obj.removeAttr('disabled');
    } else {
        obj.attr('disabled', 'disabled');
    }
}

function cast_value(val) {
    try {
        return JSON.parse(val);
    } catch (err) {
    }
    return val;
}

function get_params(callid) {
    var params = {};
    jQuery("#jsoncall_" + callid + "_params input").each(function(i, e) {
        e = jQuery(e);
        if (!e.prop('disabled')) {
            params[e.attr("name")] = cast_value(e.val());
        }
    });
    jQuery("#jsoncall_" + callid + "_params select").each(function(i, e) {
        e = jQuery(e);
        value = $('#'+e.attr("id")+' option:selected').val();
        if (!e.prop('disabled')) {
            params[e.attr("name")] = cast_value(value);
        }
    });
    return params;
}
