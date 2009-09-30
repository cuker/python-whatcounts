#!/usr/bin/env python

__version__ = "1.0"

import csv, logging
from cStringIO import StringIO
from urllib import urlencode
from urllib2 import urlopen, Request

# API_URL = "http://demo.whatcounts.com/bin/api_web"
API_URL = "http://api.whatcounts.com/bin/api_web"

log = logging.getLogger("whatcounts")

class WhatCountsError(Exception):
    def __init__(self, msgs):
        self.msgs = msgs

    def __str__(self):
        return "^".join(self.msgs)

class InvalidAddress(WhatCountsError):
    pass

class UnknownSubscriber(WhatCountsError):
    pass

def enc_value(v):
    if isinstance(v, unicode):
        v = v.encode('utf-8')
    if isinstance(v, basestring):
        return '"%s"' % v.replace('"', '\\"')
    return str(v)

class WhatCounts(object):
    def __init__(self, realm, password, api_url=API_URL):
        self._realm = realm
        self._password = password
        self._api_url = api_url

    def _encode_arg(self, v):
        if isinstance(v, unicode):
            return v.encode('utf-8')
        if isinstance(v, bool):
            return str(int(v))
        if isinstance(v, basestring):
            return v
        return unicode(v).encode('utf-8')

    def _parse_csv(self, text):
        reader = csv.DictReader(StringIO(text))
        return list(reader)

    def _request(self, command, data=None, *args, **kwargs):
        hdata = list(args)
        hdata += kwargs.items()
        hdata += [
            ('r', self._realm),
            ('p', self._password),
            ('cmd', command),
            ('output_format', 'csv'),
            ('headers', '1'),
        ]

        hdata = [(k, self._encode_arg(v)) for k, v in hdata if v is not None]

        if data:
            i = data[0]
            if isinstance(i, (list, tuple)):
                hdata.append(('data', "\n".join(",".join(x for x in data))))
            else:
                keys = i.keys()
                hdata.append(('data', "%s^%s" % (
                    ",".join(keys),
                    "^".join(
                        ",".join(enc_value(x[k]) for k in keys)
                        for x in data))))

        hdata = urlencode(hdata)

        headers = {}
        log.debug("REQUEST: %s %s %s" % (self._api_url, hdata, headers))
        req = Request(self._api_url, hdata, headers)
        res = urlopen(req)
        output = res.read()
        res.close()
        log.debug("RESPONSE: %s" % output)

        if output.startswith("FAILURE: Subscriber cannot be found") or output.startswith("FAILURE: No subscriber record exists"):
            raise UnknownSubscriber(output.split('^'))
        if output.startswith("FAILURE:") and "address does not appear to be a valid email address":
            raise InvalidAddress(output.split('^'))
        elif output.startswith("FAILURE:"):
            raise WhatCountsError(output.split('^'))
        elif output.startswith("SUCCESS:"):
            pass
        elif output.startswith('"'):
            output = self._parse_csv(output)
        elif not output:
            return []

        # TODO: Parse output
        return output

    def subscribe(self, data, list_id, format=1, force_sub=0, **kwargs):
        return self._request('subscribe', list_id=list_id, format=format, force_sub=force_sub, data=data, **kwargs)

    def update(self, data, list_id, identity_field, **kwargs):
        return self._request('update', list_id=list_id, identity_field=identity_field, data=data, **kwargs)

    def change_email(self, old_email, new_email, **kwargs):
        return self._request('change', email=old_email, email_new=new_email, **kwargs)

    def unsubscribe(self, data, list_id, optout=0, **kwargs):
        return self._request('unsubscribe', list_id=list_id, data=data, optout=optout, **kwargs)

    def delete(self, data, **kwargs):
        return self._request('delete', data=data, **kwargs)

    def find(self, email=None, first_name=None, last_name=None, identity_field=None, limit_results=None, exact_match=None, **kwargs):
        return self._request('find', email=email, first_name=first_name,
            last_name=last_name, identity_field=identity_field,
            limit_results=limit_results, exact_match=exact_match, **kwargs)

    def find_in_list(self, email=None, first_name=None, last_name=None, identity_field=None, limit_results=None, exact_match=None, **kwargs):
        return self._request('findinlist', email=email, first_name=first_name,
            last_name=last_name, identity_field=identity_field,
            limit_results=limit_results, exact_match=exact_match, **kwargs)

    def subscriber_details(self, subscriber_id, **kwargs):
        return self._request('detail', subscriber_id=subscriber_id, **kwargs)

    def create_list(self, list_name, description=None, template_id=None, from_address=None, reply_to_address=None, bounce_address=None, track_clicks=None, track_opens=None, **kwargs):
        return self._request('createlist', list_name, description=description,
            template_id=template_id, from_address=from_address,
            reply_to_address=reply_to_address, bounce_address=bounce_address,
            track_clicks=track_clicks, track_opens=track_opens, **kwargs)

    def show_lists(self, **kwargs):
        return self._request('show_lists', **kwargs)

    # TODO: Create simple/advanced Segmentation Rule (createseg)
    # TODO: Show Segmentation Rules (show_seg)
    # TODO: Update simple/advanced segmentation rule (updateseg)
    # TODO: Test segmentation rule (testseg)
    # TODO: Delete segmentation rule (deleteseg)
    # TODO: Create Template (createtemplate)
    # TODO: Show Templates (show_templates)
    # TODO: Update Template (updatetemplate)

    def show_user_events(self, subscriber_id, **kwargs):
        return self._request('show_user_events', subscriber_id=subscriber_id, **kwargs)

    def show_optouts(self, list_id, days=None, **kwargs):
        return self._request('show_opt', list_id=list_id, days=days, **kwargs)

    def show_global_optouts(self, days=None, **kwargs):
        return self._request('show_optglobal', days=days, **kwargs)

    def show_bounces(self, list_id, hard=True, days=None, **kwargs):
        return self._request('show_hard' if hard else 'show_soft', list_id=list_id, days=days, **kwargs)

    def send(self, list_id, to_address, format, from_address=None, reply_to_address=None, errors_to_address=None, virtual_mta=None, template_id=None, body=None, plain_text_body=None, html_body=None, charset=None, subject=None, data=None, **kwargs):
        """format: 1=plain text, 2=HTML, 99=MIME"""
        kwargs['from'] = from_address
        return self._request("send", list_id=list_id,
            to=to_address, format=format,
            reply_to_address=reply_to_address,
            errors_to_address=errors_to_address, vmta=virtual_mta,
            template_id=template_id, body=body,
            plain_text_body=plain_text_body, html_body=html_body,
            charset=charset, subject=subject,
            data=data, **kwargs)
