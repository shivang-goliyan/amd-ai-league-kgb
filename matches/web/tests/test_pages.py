import importlib.util
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'core'));MODULE=importlib.util.find_spec('pages')
if MODULE:import pages

class PageTests(unittest.TestCase):
    def setUp(self):self.assertIsNotNone(MODULE,'Web evidence extraction is not implemented')

    def test_table_rows_and_labels_are_preserved(self):
        page=pages.parse_page('https://example.test/specs','<h1>AX-71</h1><table><tr><th>Parameter</th><th>Value</th></tr><tr><td>Maximum temperature</td><td>87 C</td></tr></table>')
        for text in ['AX-71','Parameter','Value','Maximum temperature','87 C']:self.assertIn(text,page['text'])

    def test_json_ld_values_are_preserved(self):
        html='<script type="application/ld+json">{"@type":"Product","name":"AX-71","offers":{"price":"123.45","priceCurrency":"USD"}}</script><h1>AX-71</h1>'
        text=pages.parse_page('https://example.test/p',html)['text'];self.assertIn('123.45',text);self.assertIn('USD',text)

    def test_hidden_decoy_and_executable_scripts_are_excluded(self):
        html='<div hidden>price 999</div><p style="display: none">price 888</p><p aria-hidden="true">price 777</p><script>fetch("/delete")</script><p>Actual price 123.45</p>'
        text=pages.parse_page('https://example.test/p',html)['text'];self.assertIn('123.45',text)
        for wrong in ['999','888','777','fetch']:self.assertNotIn(wrong,text)

    def test_links_resolve_against_actual_page_url_and_deduplicate(self):
        html='<a href="../contact">Contact</a><a href="https://example.test/contact#hours">Opening hours</a>'
        p=pages.parse_page('https://example.test/company/about',html);self.assertEqual([x['url'] for x in p['links']],['https://example.test/contact'])

    def test_html_base_url_is_honored(self):
        html='<base href="/docs/"><a href="contact">Contact</a>'
        p=pages.parse_page('https://example.test/company/about',html);self.assertEqual(p['links'][0]['url'],'https://example.test/docs/contact')

    def test_unsafe_link_protocols_are_not_navigation_targets(self):
        html='<a href="javascript:alert(1)">click</a><a href="file:///etc/passwd">file</a><a href="data:text/plain,a">data</a><a href="/help">Help</a>'
        p=pages.parse_page('https://example.test/',html);self.assertEqual([x['url'] for x in p['links']],['https://example.test/help'])

    def test_phone_and_email_in_link_attributes_are_available(self):
        html='<a href="tel:+1-555-0199">Call us</a><a href="mailto:help@example.test">Email</a>'
        text=pages.parse_page('https://example.test/contact',html)['text'];self.assertIn('+1-555-0199',text);self.assertIn('help@example.test',text)

    def test_late_page_content_is_not_silently_truncated(self):
        html='<p>Navigation item</p>'*2000+'<p>Warranty period: 37 months</p>'
        self.assertIn('37 months',pages.parse_page('https://example.test/',html)['text'])

if __name__=='__main__':unittest.main()
