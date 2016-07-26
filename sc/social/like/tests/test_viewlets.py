# -*- coding: utf-8 -*-
from plone import api
from sc.social.like.browser.viewlets import SocialLikesViewlet
from sc.social.like.browser.viewlets import SocialMetadataViewlet
from sc.social.like.interfaces import ISocialLikeSettings
from sc.social.like.interfaces import ISocialLikeLayer
from sc.social.like.testing import INTEGRATION_TESTING
from sc.social.like.testing import IS_PLONE_5
from zope.interface import alsoProvides

import unittest

do_not_track = ISocialLikeSettings.__identifier__ + '.do_not_track'


class BaseViewletTestCase(unittest.TestCase):
    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        alsoProvides(self.portal.REQUEST, ISocialLikeLayer)

        with api.env.adopt_roles(['Manager']):
            self.document = api.content.create(
                self.portal, 'Document', 'my-document')

    def _get_edit_view_for_object(self, obj):
        """Return the edit view for the specified object.
        Archetypes does not have a '@@edit' view as Dexterity does.
        """
        # aliases are stored in the context of the portal_types tool
        name = self.portal.portal_types[obj.portal_type].aliases['edit']
        return obj.restrictedTraverse(name)


class MetadataViewletTestCase(BaseViewletTestCase):

    def viewlet(self, context=None):
        context = context or self.portal
        viewlet = SocialMetadataViewlet(context, self.request, None, None)
        viewlet.update()
        return viewlet

    def test_disabled_on_portal(self):
        viewlet = self.viewlet(self.portal)
        self.assertFalse(viewlet.enabled())

    def test_enabled_on_portal_with_template_full_view(self):
        # Set layout to folder_full_view
        self.portal.setLayout('folder_full_view')
        viewlet = self.viewlet(self.portal)
        self.assertTrue(viewlet.enabled())

    def test_enabled_on_document(self):
        viewlet = self.viewlet(self.document)
        self.assertTrue(viewlet.enabled())

    @unittest.skipIf(IS_PLONE_5, 'Plone 5 renders this information by default')
    def test_metadata_viewlet_disabled_on_edit_document(self):
        view = self._get_edit_view_for_object(self.document)
        self.assertNotIn('og:site_name', view())

    def test_render(self):
        viewlet = self.viewlet(self.document)
        html = viewlet.render()
        self.assertGreater(len(html), 0)


class LikeViewletTestCase(BaseViewletTestCase):

    def viewlet(self, context=None):
        context = context or self.portal
        viewlet = SocialLikesViewlet(context, self.request, None, None)
        viewlet.update()
        return viewlet

    def test_disabled_on_portal(self):
        viewlet = self.viewlet(self.portal)
        self.assertFalse(viewlet.enabled())

    def test_enabled_on_document(self):
        viewlet = self.viewlet(self.document)
        self.assertTrue(viewlet.enabled())

    def test_social_viewlet_disabled_on_edit_document(self):
        view = self._get_edit_view_for_object(self.document)
        self.assertNotIn('id="viewlet-social-like"', view())

    def test_render(self):
        viewlet = self.viewlet(self.document)
        html = viewlet.render()
        self.assertIn('id="viewlet-social-like"', html)
        self.assertIn('class="horizontal"', html)

    def test_rendermethod_default(self):
        viewlet = self.viewlet(self.document)
        self.assertEqual(viewlet.render_method, 'plugin')

    def test_rendermethod_privacy(self):
        api.portal.set_registry_record(do_not_track, True)
        viewlet = self.viewlet(self.document)
        self.assertEqual(viewlet.render_method, 'link')

    def test_rendermethod_privacy_opt_cookie(self):
        api.portal.set_registry_record(do_not_track, False)
        self.request.cookies['social-optout'] = 'true'
        viewlet = self.viewlet(self.document)
        self.assertEqual(viewlet.render_method, 'link')

    def test_rendermethod_privacy_donottrack(self):
        api.portal.set_registry_record(do_not_track, False)
        self.request.environ['HTTP_DNT'] = '1'
        viewlet = self.viewlet(self.document)
        self.assertEqual(viewlet.render_method, 'link')
